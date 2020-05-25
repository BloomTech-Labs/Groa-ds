from datetime import datetime, timedelta
import os
import logging
from random import randint
import re
import time
import requests
import pandas as pd
from bs4 import BeautifulSoup
from psycopg2.extras import execute_batch
import numpy as np

from BaseScraper import BaseScraper

class ImdbScraper(BaseScraper):

    def make_dataframe(self, movie_id, reviews, rating, titles, username,
                       found_useful_num, found_useful_den, date, review_id):
        """
        Creates a pandas dataframe from the scrape or update functions.
        """
        df = pd.DataFrame(
            {
                'movie_id': movie_id,
                'reviews': reviews,
                'rating': rating,
                'titles': titles,
                'username': username,
                'helpful_num': found_useful_num,
                'helpful_denom': found_useful_den,
                'date': date,
                'review_id': review_id
                })
        df['date'] = pd.to_datetime(df['date'])
        df['date'] = df['date'].dt.strftime('%Y-%m-%d').astype(str)
        return df

    def scrape_by_users(self, user_ids=None):
        """
            Scrapes IMDb user pages for movie ratings.
        """

        curs, conn = self.connect_to_database()

        movie_ids = set(self.get_ids())

        null_counter = 0

        if not user_ids:
            user_df = pd.read_csv("web_scraping/users.csv")
            user_ids = list(user_df["user_ids"])

        for user_id in user_ids:

            time.sleep(1.5)

            try:
                user_url = f'https://www.imdb.com/user/ur{str(user_id).zfill(8)}'
                res = requests.get(user_url)
                if res.status_code != 200:

                    # null counter is only for logging purposes
                    null_counter += 1
                    if null_counter % 100 == 0:
                        print(f"User ids {user_id-100} to {user_id} failed")
                        print(f"Latest url: {user_url}")

                    continue

                else:
                    null_counter = 0

                soup = BeautifulSoup(res.text)
                profile = soup.find(class_="user-profile")
                username = profile.find("h1").text

                print(f"Scraping reviews for user {username}")

                results_list = []
                url = f'https://www.imdb.com/user/ur{str(user_id).zfill(8)}/ratings'

                # we get existing reviews for the user so that we don't enter duplicate reviews
                query = """
                SELECT movie_id FROM movie_reviews WHERE user_name = %s;
                """
                curs.execute(query, [username])
                existing_reviews = curs.fetchall()
                existing_reviews = set(row[0] for row in existing_reviews)
                print(f"Got {len(existing_reviews)} existing reviews for user {username}")

                # iterate over ratings pages
                while True:

                    time.sleep(1.5)

                    if url.endswith("#"):
                        print(f"Found last page of user {username}")
                        break

                    res = requests.get(url)
                    if res.status_code != 200:
                        break

                    soup = BeautifulSoup(res.text, "html.parser")
                    items = soup.find_all(class_="lister-item")
                    
                    # iterate over review items
                    for item in items:

                        head = item.find(class_="lister-item-header")
                        movie_id = head.find("a").get("href").strip("/").strip("title/tt")
                        if movie_id not in movie_ids:
                            continue
                        if movie_id in existing_reviews:
                            continue

                        ratings = item.find(class_="ipl-rating-widget")
                        user_ratings = ratings.find(class_="ipl-rating-star--other-user")
                        stars = user_ratings.find(class_="ipl-rating-star__rating")
                        rating = int(stars.text)//2

                        text_muteds = item.find_all(class_="text-muted")
                        date_text = None
                        for text in text_muteds:
                            if text.text.startswith("Rated on"):
                                date_text = text.text
                                break
                        if date_text:
                            date_text = date_text.strip("Rated on")
                            date = datetime.strptime(date_text, "%d %b %Y")
                        else:
                            date = None

                        results_list.append((movie_id, date, rating, username, url))
                        print("Got results:", results_list[-1])

                    # end for loop

                    next_button = soup.find(class_="next-page")
                    if not next_button:
                        url = "#"
                    else:
                        url = "https://www.imdb.com" + next_button.get("href")


                # end while loop

                print(f"Got {len(results_list)} reviews")

                query = """
                INSERT INTO movie_reviews (
                    movie_id,
                    review_date,
                    user_rating,
                    user_name,
                    source
                )
                VALUES (%s, %s, %s, %s, %s);
                """

                try:
                    # execute query
                    execute_batch(curs, query, results_list)
                    conn.commit()
                except:
                    curs, conn = self.connect_to_database()
                    execute_batch(curs, query, results_list)
                    conn.commit()


                print()

            except Exception as e:
                curs, conn = self.connect_to_database()
                print("UNHANDLED EXCEPTION")
                print(e)
                continue

    def update(self):
        curs, conn = self.connect_to_database()
        ids = self.pull_ids(save=False)

        review_ids = set(rid for rid, _ in ids)
        movie_ids = set(mid for _, mid in ids)

        user_ids = set()

        print("Updating...")
        for mid in movie_ids:
            reviews = []
            url = f'http://www.imdb.com/title/tt{mid}/reviews?sort=submissionDate&dir=desc&ratingFilter=0'
            print("Scraping movie", url)
            while url is not None:

                try:
                    counter = 0
                    while counter < 5:
                        counter += 1
                        response = requests.get(url)
                        if response.status_code == 200:
                            break
                        time.sleep(1)
                    soup = BeautifulSoup(response.text, "html.parser")
                    # items holds all the HTML for the webpage
                    items = soup.find_all(class_='lister-item-content')
                except Exception as e:
                    print("Unhandled exception in soup")
                    print(e)
                    continue

                for item in items:

                    try:
                        # get the review ID
                        raw_revid = (item.find(class_="title").get("href"))
                        match = re.search(r'rw\d+', raw_revid)
                        review_id = match.group()
                        # print(f"review ID from IMBd: {review_id}")
                        # check whether or not the review ID is in the DB
                        review_id = review_id.strip("rw")
                        review_id = int(review_id)
                        if review_id in review_ids:
                            continue

                        print("Found new review")

                        # populate lists
                        review_text = item.find(class_="text show-more__control").get_text()
                        title = item.find(class_="title").get_text()

                        username = item.find(class_="display-name-link").get_text()
                        user_id_href = item.find(class_="display-name-link").find("a").get("href")
                        user_id = re.search(r"ur(?P<user_id>\d+)", user_id_href).group("user_id")
                        user_ids.add(user_id)

                        date_str = item.find(class_="review-date").get_text()
                        date = datetime.strptime(date_str, "%d %B %Y")
                        found_useful = item.find(class_="actions text-muted").get_text()
                        found_useful = found_useful.replace(",", "")
                        usefuls = [int(i) for i in found_useful.split() if i.isdigit()]

                        try:
                            rating = item.find(class_="rating-other-user-rating").find('span').text
                        except Exception:
                            rating = None
                        # for loop ends here

                        reviews.append((
                            review_id,
                            mid,
                            review_text,
                            title,
                            username,
                            date,
                            rating,
                            url
                        ))
                        review_ids.add(review_id)

                    except Exception as e:
                        print("Unhandled exception in scraping")
                        print(e)
                        url = None
                        continue

                # loading more data if there are more than 25 reviews
                try:
                    load = soup.find(class_='load-more-data')
                    key = load["data-key"]
                    print("Found another page of reviews")
                    url = f'http://www.imdb.com/title/tt{mid}/reviews/_ajax?paginationKey={key}'

                    time.sleep(randint(1, 3))
                except Exception as e:
                    print("Exception in loading")
                    print(e)
                    url = None

            # end while loop
            if reviews:
                inner_counter = 0
                while True:
                    try:
                        query = """
                        INSERT INTO movie_reviews (
                            review_id,
                            movie_id,
                            review_text,
                            review_title,
                            user_name,
                            review_date,
                            user_rating,
                            source
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
                        """
                        execute_batch(curs, query, reviews)
                        conn.commit()
                        print(f"Inserted {len(reviews)} reviews in db\n")
                        break

                    except Exception as e:
                        if inner_counter < 3:
                            print("Error inserting rows, trying again")
                            print(e)
                            curs, conn = self.connect_to_database()
                            inner_counter += 1
                            continue
                        else:
                            print("Giving up")
                            break

        self.scrape_by_users(user_ids=list(user_ids))


    def pull_ids(self, save=True, filename=False):
        '''
        Connects to the database and returns all ids as a list.

        Returns a list of review and movie ids. Pass save=False if
        you don't want to make a new file with the ids.
        '''
        self.start_timer()
        print("Connecting to database...")
        try:
            # connect to the database and query it for the review/movie ids
            cursor, connection = self.connect_to_database()
            print("Connected.")
            query = "SELECT review_id, movie_id FROM movie_reviews"
            cursor.execute(query)
            # put all of the review/movie ids into a list of tuples
            print("Fetching IDs...")
            self.ids = cursor.fetchall()
            cursor.close()
            connection.close()
            print("Done.")
        except Exception as e:
            print(e)

        elapsed = self.end_timer()
        elapsed = self.convert_time(elapsed)

        self.start_timer()

        # save the IDs to a file
        if save:
            # if you pass in a filename, use that otherwise use the default
            filename = input("Enter a filename: ") if filename else "review_ids.csv"

            with open(filename, 'w') as file:
                for rev, mov in self.ids:
                    # print(type(rev))
                    # print(rev[:5])
                    # print(mov[:5])
                    file.write(str(rev + "," + mov) + "\n")
            finished = self.end_timer()
            finish = self.convert_time(finished)
            # class variable used to load the file before program is terminated
            self.load_path = os.path.join(os.getcwd(), filename)
            print(f"File saved to {self.load_path} and was saved in {finish}")

        print(f"Retrieved {cursor.rowcount} review/movie ID's in {elapsed}")
        print(f"The ID's are stored as {type(self.ids)}")
        print(f"The first 10 entries are:\n{self.ids[:10]}")

        return self.ids
