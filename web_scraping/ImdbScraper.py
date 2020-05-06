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

    def scrape(self):
        """
        Scrapes imbd.com for user review pages.

        create_log, make_dataframe, and insert_rows are intended to be
        used inside this function. Takes in the id of the movie in
        "ttxxxxxxx" format, robust to different numbers of numerals.
        Fails gracefully on movies with no reviews, moving on without
        returning anything.
        """
        id_list = self.get_ids()

        t = time.perf_counter()
        movie_id = []
        rating = []
        reviews = []
        titles = []
        username = []
        found_useful_num = []
        found_useful_den = []
        date = []
        review_id = []
        iteration_counter = 0
        broken = []

        for count, id in enumerate(id_list):
            try:
                t1 = time.perf_counter()
                Nan_count = 0
                review_count = 0
                movie_title = ''

                # self.locate(id)

                url_short = f'http://www.imdb.com/title/{id}/'
                url_reviews = url_short + 'reviews?ref_=tt_urv'

                time.sleep(randint(3, 6))
                response = requests.get(url_reviews)
                if response.status_code != 200:
                        response = requests.get(url_reviews)
                        if response.status_code != 200:
                            print(f"call to {url_reviews} failed with status \
code {response.status_code}!")
                            continue
                soup = BeautifulSoup(response.text, 'html.parser')
                items = soup.find_all(class_='lister-item-content')
                print(f"ID: {id} at index {self.all_ids.index(id)}")

                while True:
                    if iteration_counter >= self.max_iter_count:
                        df = self.make_dataframe(movie_id, reviews, rating,
                                                 titles, username,
                                                 found_useful_num,
                                                 found_useful_den,
                                                 date, review_id)
                        self.insert_rows(df)
                        movie_id.clear()
                        rating.clear()
                        reviews.clear()
                        titles.clear()
                        username.clear()
                        found_useful_num.clear()
                        found_useful_den.clear()
                        date.clear()
                        review_id.clear()
                        iteration_counter = 0
                        df = df.iloc[0:0]

                    # populate lists
                    for item in items:
                        review_count += 1
                        reviews.append(item.find(class_="text show-more__control").get_text())
                        titles.append(item.find(class_="title").get_text())
                        username.append(item.find(class_="display-name-link").get_text())
                        date.append(item.find(class_="review-date").get_text())
                        movie_id.append(id.replace("tt", ""))
                        found_useful = item.find(class_="actions text-muted").get_text()
                        found_useful = found_useful.replace(",", "")
                        usefuls = [int(i) for i in found_useful.split() if i.isdigit()]
                        found_useful_num.append(usefuls[0])
                        found_useful_den.append(usefuls[1])
                        raw_revid = (item.find(class_="title").get("href"))
                        match = re.search('rw\d+', raw_revid)
                        try:
                            review_id.append(match.group())
                        except Exception:
                            review_id.append('')
                        try:
                            rating.append(item.find(class_="rating-other-user-rating").find('span').text)
                        except Exception:
                            rating.append(11)
                            Nan_count += 1
                        # for loop ends here
                    # loading more data if there are more than 25 reviews
                    load = soup.find(class_='load-more-data')
                    if items:
                        iteration_counter += 1
                    try:
                        key = load['data-key']
                        # exists only if there is a "load More" button
                    except Exception:
                        break  # Go to next movie id
                    url_reviews = url_short + 'reviews/_ajax?paginationKey=' + key
                    time.sleep(randint(3, 6))
                    response = requests.get(url_reviews)
                    soup = BeautifulSoup(response.text, 'html.parser')
                    items = soup.find_all(class_='lister-item-content')
                    # while loop ends here

                # time took to scrape each movie
                t2 = time.perf_counter()
                finish = t2-t1

                # if the logfile exist already within the first iteration
                # it will be deleted and recreated which fixes the issue of
                # duplicating info when ran several times
                if count == 0 and os.path.exists(f"Logfile{self.scraper_instance}.txt"):
                    os.remove(f"Logfile{self.scraper_instance}.txt")

                # log the movie

                # self.create_log(id, review_count, Nan_count, finish)

                # for loop ends here

            # catches any error and lets you know which ID was the last one scraped
            except Exception as e:
                broken.append(id)
                continue

        # create DataFrame
        df = self.make_dataframe(movie_id, reviews, rating, titles, username,
                                 found_useful_num, found_useful_den, date,
                                 review_id)
        self.insert_rows(df)

        # total time it took to scrape each review
        t3 = time.perf_counter()
        total = t3 - t
        print(f"Scraped {count + 1} movies in {round(total,2)} seconds")

        print('All done!\n')
        print("The following IDs were not scraped succcessfully:")
        self.show(broken)


    def scrape_by_users(self):
        """
            Scrapes IMDb user pages for movie ratings.
        """

        curs, conn = self.connect_to_database()

        movie_ids = set(self.get_ids())

        null_counter = 0

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
        '''
        Scrapes IMDB for reviews, then adds only new reviews.

        Process:
        1) Each unique movie ID is used to search IMBd for its movie, and
        the reviews are sorted by recency.
        2) The top review will have its ID checked against review IDs in
        the database to see if there is a match.
        3) If there isn't a match (meaning that the review ID is not yet
        in the list of review IDs) that review will be saved and step 2
        will be repeated with the next review on the page.
        4) Once the function comes across a review with its review ID
        already in the database, it will be the last review scraped for
        that movie ID and the whole process is repeated with the next
        unique movie ID.
        '''
        ids = self.pull_ids(save=False)
        review_ids = []
        movie_ids = []

        # seperate reviews and movies
        for rid, mid in ids:
            review_ids.append(str(rid))
            movie_ids.append(str(mid))
        # only unique movies
        unique_movie_ids = set(movie_ids)
        unique_movie_ids = list(unique_movie_ids)
        unique_movie_ids.sort()
        print(f"There are {len(unique_movie_ids)} unique movie IDs")
        print(f"The first 10 unique IDs are: \n{unique_movie_ids[:10]}\n")
        movie_id = []
        rating = []
        reviews = []
        titles = []
        username = []
        found_useful_num = []
        found_useful_den = []
        date = []
        new_review_id = []
        iteration_counter = 0
        broken = []
        self.start_timer()
        # Start the process described
        print("Updating...")
        for id in unique_movie_ids:
            try:
                Nan_count = 0
                review_count = 0
                movie_title = ''
                num = id
                id = "tt" + id
                url_short = f'http://www.imdb.com/title/{id}/'
                # sort the reviews by date
                url_reviews = url_short + 'reviews?sort=submissionDate&dir=\
desc&ratingFilter=0'
                time.sleep(randint(3, 6))
                response = requests.get(url_reviews)
                if response.status_code != 200:
                        response = requests.get(url_reviews)
                        if response.status_code != 200:
                            print(f"call to {url_reviews} failed with status \
code {response.status_code}!")
                            continue
                soup = BeautifulSoup(response.text, 'html.parser')
                # items holds all the HTML for the webpage
                items = soup.find_all(class_='lister-item-content')
                while True:
                    if iteration_counter >= self.max_iter_count:
                        df = self.make_dataframe(movie_id, reviews, rating,
                                                 titles, username,
                                                 found_useful_num,
                                                 found_useful_den,
                                                 date, new_review_id)
                        self.insert_rows(df)
                        movie_id.clear()
                        rating.clear()
                        reviews.clear()
                        titles.clear()
                        username.clear()
                        found_useful_num.clear()
                        found_useful_den.clear()
                        date.clear()
                        new_review_id.clear()
                        iteration_counter = 0
                        df = df.iloc[0:0]

                    for item in items:
                        # get the review ID
                        raw_revid = (item.find(class_="title").get("href"))
                        match = re.search(r'rw\d+', raw_revid)
                        review_id = match.group()
                        # print(f"review ID from IMBd: {review_id}")
                        # check whether or not the review ID is in the DB
                        if review_id not in review_ids:
                            print(f"Updating {id} at index \
{unique_movie_ids.index(num)} in the database for review ID {review_id}")
                            review_count += 1

                            # populate lists
                            reviews.append(item.find(class_="text show-more__control").get_text())
                            titles.append(item.find(class_="title").get_text())
                            username.append(item.find(class_="display-name-link").get_text())
                            date.append(item.find(class_="review-date").get_text())
                            movie_id.append(id.replace("tt", ""))
                            found_useful = item.find(class_="actions text-muted").get_text()
                            found_useful = found_useful.replace(",", "")
                            usefuls = [int(i) for i in found_useful.split() if i.isdigit()]
                            found_useful_num.append(usefuls[0])
                            found_useful_den.append(usefuls[1])
                            raw_revid = (item.find(class_="title").get("href"))
                            match = re.search(r'rw\d+', raw_revid)
                            try:
                                new_review_id.append(match.group())
                            except Exception:
                                new_review_id.append('')
                            try:
                                rating.append(item.find(class_="rating-other-user-rating").find('span').text)
                            except Exception:
                                rating.append(11)
                                Nan_count += 1
                            # for loop ends here

                    # loading more data if there are more than 25 reviews
                    load = soup.find(class_='load-more-data')
                    if items:
                        iteration_counter += 1
                    try:
                        key = load['data-key']
                        # exists only if there is a "load More" button
                    except Exception:
                        break  # End the while loop and go to next movie id
                    url_reviews = url_short + 'reviews/_ajax?paginationKey=' + key

                    time.sleep(randint(3, 6))
                    response = requests.get(url_reviews)
                    soup = BeautifulSoup(response.text, 'html.parser')
                    items = soup.find_all(class_='lister-item-content')
                    # while loop ends here

            except Exception as e:
                print(e, "In update function")
                continue

        print("Updated.")
        # create DataFrame
        df = self.make_dataframe(movie_id, reviews, rating, titles, username,
                                 found_useful_num, found_useful_den,
                                 date, review_id)
        df.drop_duplicates(inplace=True)

        self.insert_rows(df)

        elapsed = self.end_timer()
        elapsed = self.convert_time(elapsed)
        print(f"finished in {elapsed}")

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
