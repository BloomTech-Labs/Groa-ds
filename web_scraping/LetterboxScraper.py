from bs4 import BeautifulSoup
import sys
import time
from random import randint
import re
import requests
import pandas as pd
from psycopg2.extras import execute_batch
import traceback
import queue
from datetime import datetime


from BaseScraper import BaseScraper

class LetterboxScraper(BaseScraper):

    def scrape(self):
        """
        Scrapes letterboxd.com for review pages.

        Works very similarly to the basic scrape function. Takes in ids
        from imdb and checks to see if they exist on letterboxd. If
        not, it will hit an exception and move on. Movies with no
        reviews also hit an exception. This is much slower than imbd
        due to differing website design.
        """
        id_list = self.get_ids()
        t = time.perf_counter()
        movie_id = []
        rating = []
        reviews = []
        username = []
        likes = []
        date = []
        review_id = []
        iteration_counter = 0
        broken = []
        page_count = 0

        query = """
        SELECT movie_id, primary_title FROM movies
        """
        curs, conn = self.connect_to_database()
        curs.execute(query)
        fetched = curs.fetchall()
        movie_ids = set([row[0] for row in fetched])
        movie_titles = {row[0]: row[1] for row in fetched}

        for count, id in enumerate(id for id in id_list if id in movie_ids):
            print("----------------------------------------")
            try:
                t1 = time.perf_counter()

                review_count = 0

                # self.locate(id)

                url_initial = f"https://www.letterboxd.com/imdb/{id}"
                time.sleep(randint(3, 6))
                initial_response = requests.get(url_initial)
                title = ""
                try:
                    soup = BeautifulSoup(initial_response.text, 'html.parser')
                    title = soup.find(class_="headline-1 js-widont prettify").get_text()
                    title = title.replace(" ", "-").lower()
                    print("Found: ", title, movie_titles[id])

                except Exception as e:
                    print(f"Unable to find a title for this movie at index: {id}")
                    print("This is normal and expected behavior")
                    raise Exception(e)
                url_reviews = initial_response.url + 'reviews/by/activity/'
                print(url_reviews)
                # initially, I wanted to make this sorted by recency, but if
                # there are fewer than 12 reviews only sorting by popular is
                # available
                time.sleep(randint(3, 6))
                response = requests.get(url_reviews)
                if response.status_code != 200:
                        time.sleep(randint(3, 6))
                        response = requests.get(url_reviews)
                        if response.status_code != 200:
                            print(f"call to {url_reviews} failed with status \
code {response.status_code}!")
                            continue

                soup = BeautifulSoup(response.text, 'html.parser')
                items = soup.find_all(class_='film-detail')
                if len(items) == 0:
                    print(f"No reviews for {id} {title}")
                    continue
                print(f"ID: {id} at index {self.all_ids.index(id)}")
                while True:
                    if iteration_counter >= self.max_iter_count:
                        df = self.letterboxd_dataframe(movie_id, review_id,
                                                       rating, reviews, date,
                                                       username)
                        self.letterboxd_insert(df)
                        movie_id.clear()
                        rating.clear()
                        reviews.clear()
                        username.clear()
                        likes.clear()
                        date.clear()
                        review_id.clear()
                        df = df.iloc[0:0]
                        iteration_counter = 0
                    iteration_counter += 1
                    for item in items:
                        body = item.find(class_="body-text -prose collapsible-text")
                        append = body['data-full-text-url']
                        if item.find(class_="reveal js-reveal") or item.find(class_="collapsed-text"):
                            text_url = 'https://www.letterboxd.com' + append
                            time.sleep(randint(3, 4))
                            fulltext = requests.get(text_url)
                            if fulltext.status_code != 200:
                                time.sleep(randint(3, 6))
                                fulltext = requests.get(text_url)
                                if fulltext.status_code != 200:
                                    print(f"call to {text_url} failed with \
status code {fulltext.status_code}!")
                                    continue
                            fulltext = re.sub(r'\<[^>]*\>', "", fulltext.text)
                            reviews.append(fulltext)

                        else:
                            reviews.append(body.get_text())
                        review_count += 1
                        movie_id.append(id.replace("tt", ""))
                        append = append.split(":", 1)[1].replace("/", "")
                        review_id.append(append)

                        try:
                            rating1 = str(item.find(class_="attribution"))
                            found = re.search(r'rating -green rated-\d+', rating1)
                            found = found.group()
                            text = found.split("-")
                            rate = int(text[-1])
                            rating.append(rate)
                        except Exception:
                            rating.append(11)
                        username.append(item.find(class_="name").get_text())

                        if item.find('span', '_nobr').get_text():
                            dates = item.find('span', '_nobr').get_text()
                            date.append(dates)
                        else:
                            datetime = str(item.find('time', class_="localtime-dd-mmm-yyyy"))
                            extract = datetime.split('"')
                            dates = str(extract[3])
                            date.append(dates[:10])

                    if soup.find('a', class_="next"):
                        page_count += 1
                        url_more = url_reviews + 'page/' + str(page_count+1) + '/'
                        print(url_more)
                        time.sleep(randint(3, 6))
                        response = requests.get(url_more)
                        if response.status_code != 200:
                            time.sleep(randint(3, 6))
                            response = requests.get(url_more)
                            if response.status_code != 200:
                                print(f"call to {url_more} failed with status \
code {response.status_code}!")
                                continue
                        soup = BeautifulSoup(response.text, 'html.parser')
                        items = soup.find_all(class_='film-detail')
                    else:
                        print('end of this movie')
                        page_count = 0
                        break
                    # While loop ends here

                t2 = time.perf_counter()
                finish = t2-t1

                # if count == 0 and os.path.exists(f"Logfile{self.scraper_instance}.txt"):
                #     os.remove(f"Logfile{self.scraper_instance}.txt")
                # print("Logging")
                # self.create_log(title,review_count,None,finish)

            except Exception as e:
                broken.append(id)
                print("Broken!", id)
                err1, err2, tb = sys.exc_info()
                print(err1, err2)
                print(traceback.print_tb(tb))
                continue

        try:
            df = self.letterboxd_dataframe(movie_id, review_id, rating,
                                           reviews, date, username)
            self.letterboxd_insert(df)
        except Exception as e:
            print("error while creating dataframe or inserting into database")
            raise Exception(e)

        t3 = time.perf_counter()
        total = t3 - t
        print(f"Scraped {count + 1} movies in {round(total,2)} seconds")
        print('All done!\n')
        print("The following IDs were not scraped succcessfully:")
        self.show(broken)
        if len(broken) == 0:
            print("none")

    def scrape_by_users(self, first_user="flyingindie"):
        """
            Scrapes all movies rated or reviewed by `first_user`,
            then moves to users connected to `first_user` and scrapes
            movies rated by them, and so on.
        """

        print("scrape_by_users()")
        base_url = "https://letterboxd.com"

        # high priority is a list of users with no reviews currently in the db
        high_priority = []
        # low priority is a list of users with existing reviews in the db
        low_priority = [first_user]

        curs, conn = self.connect_to_database()
        curs.execute("SELECT movie_id, primary_title, original_title, start_year FROM movies;")
        fetched = curs.fetchall()

        print("Got movie ids")

        title_to_id = {
            (row[1], row[3]): row[0]
            for row in fetched
        }
        title_to_id.update({
            (row[2], row[3]): row[0]
            for row in fetched
        })

        curs.execute("SELECT COUNT(DISTINCT user_name) FROM movie_reviews;")
        num_users = curs.fetchone()[0]
        print(f"Found {num_users} distinct users")
        step = 100_000
        existing_users = set()
        for ix in range(0, num_users+1, step):
            curs.execute("SELECT DISTINCT user_name FROM movie_reviews LIMIT %s OFFSET %s;", (ix, step))
            fetched = curs.fetchall()
            existing_users.update(set(row[0] for row in fetched))
            print(f"retrieved {len(existing_users)} existing users")

        counter = 0
        visited = set()

        while high_priority or low_priority:

            if counter >= self.max_iter_count:
                print("Reached max iterations")
                break

            try:
                curs, conn = self.connect_to_database()

                if high_priority:
                    print(f"Getting user from high_priority out of {len(high_priority)} total users")
                    ix = randint(0, len(high_priority)-1)
                    username = high_priority.pop(ix)


                elif low_priority:
                    print(f"Getting user from low_priority out of {len(low_priority)} total users")
                    ix = randint(0, len(low_priority)-1)
                    username = low_priority.pop(ix)

                if username in visited:
                    continue

                if username in existing_users:

                    query = """
                        SELECT movie_id
                        FROM movie_reviews
                        WHERE user_name=%s;
                    """
                    curs.execute(query, [username])
                    existing_reviews = set(row[0] for row in curs.fetchall())
                    print(f"Got {len(existing_reviews)} existing reviews for user {username}")

                else:
                    existing_reviews = set()

                visited.add(username)
                counter += 1

                if counter % 50 == 0:
                    high_priority = list(set(high_priority))
                    low_priority = list(set(low_priority))

                print(f"scraping user: {username}")

                url = base_url + "/" + username + "/films/reviews/"
                reviews = []

            except Exception as e:
                print(f"Exception initializing scraping for this page")
                print(e)
                continue

            while url is not None:

                try:
                    res = requests.get(url)
                    if res.status_code != 200:
                        print(f"Failed to scrape user: {url}")
                        continue

                    print(f"Scraping {url}")

                    soup = BeautifulSoup(res.text, "html.parser")

                    films = soup.find_all(class_="film-detail")

                except Exception as e:
                    print("Error in requests or beautifulsoup")
                    print(e)

                    url = None
                    continue

                for film in films:

                    try:
                        headline = film.find("h2")
                        title, year = headline.find_all("a")
                        movie_id = title_to_id.get((title.text, int(year.text)))
                        if not movie_id:
                            continue
                        if movie_id in existing_reviews:
                            continue

                        rating_el = film.find(class_="rating")
                        if not rating_el:
                            print("No rating")
                            rating = None
                        else:
                            rating = len(rating_el.text)

                        text_el = film.find(class_="body-text")
                        if not rating_el:
                            print("No review text")
                            text = None
                        else:
                            text = text_el.text

                    except Exception as e:
                        print(f"scrape_by_users(): unhandled exception getting rating or text")
                        print(e)
                        continue

                    try:
                        date_text = film.find(class_="date").text
                        date = date_text.strip("Watched ").strip("Rewatched ").strip("Added ")
                        if date: 
                            dt = datetime.strptime(date, "%d %b, %Y")
                        else:
                            dt = pd.to_datetime(film.find(class_="date").find("time").get("datetime"))
                    except Exception as e:
                        print(f"scrape_by_users(): unhandled exception getting date: {date_text}")
                        print(e)
                        dt = None
                    
                    reviews.append((
                        movie_id,
                        dt,
                        rating,
                        text,
                        username,
                        "letterboxd",
                    ))

                # end for

                try:
                    next_button = soup.find("a", class_="next")
                    if next_button is not None:
                        url = base_url + next_button.get("href")
                    else:
                        url = None

                    time.sleep(1.5)

                except Exception as e:
                    print(f"scrape_by_users(): unhandled exception getting next button")
                    print(e)
                    url = None

            # end while
            
            inner_counter = 0
            while True:
                try:
                    query = """
                    INSERT INTO movie_reviews (
                        movie_id,
                        review_date,
                        user_rating,
                        review_text,
                        user_name,
                        source
                    )
                    VALUES (%s, %s, %s, %s, %s, %s);
                    """
                    execute_batch(curs, query, reviews)
                    conn.commit()
                    existing_users.add(username)
                    print(f"Inserted {len(reviews)} reviews in db\n")
                    break

                except Exception as e:
                    if inner_counter < 3:
                        print("Error inserting rows, trying again")
                        curs, conn = self.connect_to_database()
                        inner_counter += 1
                        continue
                    else:
                        print("Giving up")
                        break


            try:
                # networking: add users that the current user is following
                url = base_url + "/" + username + "/following"
                while url is not None:
                    print(f"Getting network on page {url}")
                    res = requests.get(url)
                    if res.status_code != 200:
                        break

                    soup = BeautifulSoup(res.text, "html.parser")

                    for person in soup.find_all(class_="table-person"):
                        title = person.find(class_="title-3")
                        href = title.find("a").get("href")
                        username = href.strip("/")
                        if username in visited:
                            continue

                        if username in existing_users:
                            low_priority.append(username)
                        else:
                            high_priority.append(username)

                    next_button = soup.find(class_="next")
                    if not next_button or not next_button.get("href"):
                        print("Finish networking")
                        break
                    url = base_url + next_button.get("href")

                    time.sleep(1)

            except Exception as e:
                print("Failed networking")
                print(e)

            print("\n\n")

        # end while



                    



    def letterboxd_dataframe(self, movie_id, review_id,
                             ratings, reviews, date, username):
        """
        Used in scrape_letterboxd to make and return a dataframe.
        """
        df = pd.DataFrame(
            {
                'movie_id': movie_id,
                'review_text': reviews,
                'user_rating': ratings,
                'username': username,
                'review_date': date,
                'review_id': review_id
                })
        df['review_date'] = pd.to_datetime(df['review_date'], errors='coerce')
        df['review_date'] = df['review_date'].fillna(method='ffill')
        df['review_date'] = df['review_date'].fillna(value='2012-12-21')
        df['review_date'] = df['review_date'].dt.strftime('%Y-%m-%d')
        print(df['review_date'])
        return df

    def letterboxd_insert(self, df):
        """
        Connects to the database and inserts reviews as new rows.

        Takes a dataframe and formats it into a very long string to
        convert to  SQL. Connects to the database, executes the query,
        and closes the cursor and connection.
        """
        # convert rows into tuples
        row_insertions = []
        for i in list(df.itertuples(index=False)):
            row_insertions.append((
                    i.movie_id,
                    i.review_date,
                    float(i.user_rating),
                    str(i.username),
                    str(i.review_text),
                    "letterboxd",
            ))
        row_insertions = row_insertions[:-2]
        cursor_boi, connection = self.connect_to_database()
        # create SQL INSERT query
        query = """
        INSERT INTO movie_reviews(movie_id, review_date, user_rating, user_name, review_text, source)
        VALUES (%s, %s, %s, %s, %s, %s);
        """
        # execute query
        execute_batch(
            cursor_boi,
            query,
            row_insertions,
        )
        connection.commit()
        cursor_boi.close()
        connection.close()
        print("Insertion Complete")

