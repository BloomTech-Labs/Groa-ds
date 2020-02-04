from datetime import datetime, timedelta
from getpass import getpass
import logging
import os
from random import randint
import re
import sys
import time

from bs4 import BeautifulSoup # 4.8.2
from decouple import config # 3.3
import pandas as pd # 0.25.0
import psycopg2 # 2.8.4
import requests # 2.22.0
# python 3.7.5

class Scraper():
    """
    Scrapes IMDB, Letterboxd, and finder.

    Start and end parameters are inclusive. max_iter controls how
    many loops can be run before the program inserts into the
    database. This indirectly controls the size and frequency of
    insertions. scraper_instance must be unique for each instance
    of the program to ensure their log files do not mess each other
    up. Necessary environment variables are PASSWORD, HOST, PORT,
    and FILENAME.
    """

    def __init__(self, start, end, max_iter, scraper_instance):
        self.start = start
        self.end = end + 1
        self.current_ids = []
        self.all_ids = []
        self.range = 0
        self.pickup = 0
        self.max_iter_count = max_iter
        self.scraper_instance = scraper_instance
        self.database = "postgres"
        self.user = "postgres"
        self.password = config("PASSWORD")
        self.host = config("HOST")
        self.port = config("PORT")
        self.filename = config("FILENAME")

    def connect_to_database(self):
        """
        Connects to the database.

        Uses class variables set from the environment and takes no
        arguments other than self. Returns a cursor object and a
        connection object.
        """
        connection = psycopg2.connect(
            database = self.database,
            user     = self.user,
            password = self.password,
            host     = self.host,
            port     = self.port
            )
        return connection.cursor(), connection

    def get_ids(self):
        '''
        Looks for a csv and converts it to a list of movie ids.

        Takes in the path to a file to read into a dataframe.
        Uses a class variable set from environment variable
        FILENAME to look for a csv formatted after the tarball
        released by IMDB.com. Returns a list.
        '''
        df = pd.read_csv(self.filename, encoding='ascii', header=None)

        # get all the rows from the second column and then select only
        # the ones from the start and end positions
        id_list = [row for row in df.iloc[:, 1]]
        self.all_ids = id_list

        id_list = id_list[self.start:self.end]
        self.current_ids = id_list

        # lets the class know the range of ID's its grabbing at a time
        if self.start > self.end:
            raise ValueError("The start position needs to be \
less than the end position")
        self.range = abs(self.end - self.start)

        return id_list

    def show(self, lst):
        '''
        Outputs any list in a formatted output.
        '''
        for count, index in enumerate(lst):
            print(f"{count+1}) {index}")

    def create_log(self, movie_name, num_review, num_nan, elapsed):
        """
        Creates a log for each movie scraped.

        Takes info generated within imdb_scraper to produce a log file to
        return a log of the movie name, the number of reviews,
        and the time taken
        """
        directory = os.getcwd()
        os.chdir(directory)
        movie_name = movie_name.replace("-", " ")
        with open(f'Logfile{self.scraper_instance}.txt', 'a+') as file:
            file.write("--------------------------------------------------\n")
            file.write(str(datetime.now()) + "\n")
            file.write(f"Movie: {movie_name}\n")
            file.write(f"This movie has {num_review} reviews\n")
            file.write(f"Out of {num_review} reviews there were \
                         {num_nan} with NaN ratings\n")
            file.write(f"Finished Scraping {movie_name} in \
                         {round(elapsed,2)} seconds\n")
            file.write("--------------------------------------------------")
            file.write("\n")

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

    def locate(self, last_id):
        '''
        This function takes in the last id used for scraping and tells
        you its index in the master list of movie ids and the curent ids
        being used. it also will tell you how many more ids there are
        left to scrape.
        '''
        self.pickup = self.all_ids.index(last_id)

        # writes the last used ID to a file
        with open("pickup.txt", 'w') as file:
            file.write(str(self.pickup+1))
            file.write("\n")
            file.write(str(self.end))

    def insert_rows(self, df):
        """
        Connects to the database and inserts reviews as new rows.
        Takes a dataframe and formats it into a very long string to
        convert to SQL. Connects to the database, executes the query,
        and closes the cursor and connection.
        """
        # convert rows into tuples
        row_insertions = ""
        for i in list(df.itertuples(index=False)):
            row_insertions += str((
                              str(i.username.replace("'", "").replace('"', '')),
                              i.movie_id,
                              i.date,
                              str(i.reviews.replace("'", "").replace('"', '')),
                              str(i.titles.replace("'", "").replace('"', '')),
                              int(i.rating),
                              i.helpful_num,
                              i.helpful_denom,
                              i.review_id)) + ", "

        # remove hanging comma
        row_insertions = row_insertions[:-2]
        cursor_boi, connection = self.connect_to_database()
        # create SQL INSERT query
        query = """INSERT INTO reviews(username,
                                    movie_id,
                                    review_date,
                                    review_text,
                                    review_title,
                                    user_rating,
                                    helpful_num,
                                    helpful_denom,
                                    review_id)
                                    VALUES """ + row_insertions + ";"

        # execute query
        cursor_boi.execute(query)
        connection.commit()
        cursor_boi.close()
        connection.close()
        print("Insertion Complete")

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
            query = "SELECT review_id, movie_id FROM reviews"
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

    def start_timer(self):
        """
        Starts a timer.
        """
        self.begin = time.perf_counter()

    def end_timer(self):
        '''
        Ends the timer started by start_timer.
        '''
        self.done = time.perf_counter()
        self.elapsed = self.done - self.begin
        return self.elapsed

    def convert_time(self, elapsed):
        '''
        Converts seconds into HH:MM:SS format.
        '''
        e = str(timedelta(seconds=elapsed))
        return e

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
        ids = pull_ids(save=False)
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

    def load_ids(self, path=None):
        '''
        Loads ids from a saved file.

        This function can only be ran before the program is terminated.
        It uses the class variable self.load_path to locate the saved
        file with the review/movie IDs and automatically loads the data
        from that file back into the class variable self.ids.
        '''

        path = self.load_path if path is None else path

        df = pd.read_csv(path, header=None)
        self.ids = df.values.tolist()
        return self.ids

    def scrape_letterboxd(self):
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

        for count, id in enumerate(id_list):
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

                except Exception as e:
                    print(f"Unable to find a title for this movie at index: \
{self.all_ids.index(id)}")
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
                print(sys.exc_info()[1])
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
        row_insertions = ""
        for i in list(df.itertuples(index=False)):
            row_insertions += str((i.movie_id,
                                   i.review_date,
                               int(i.user_rating),
                               str(i.review_text.replace("'", "").replace('"', '')),
                                   i.review_id,
                               str(i.username.replace("'", "").replace('"', '')))) + ", "
        # remove hanging comma
        row_insertions = row_insertions[:-2]
        cursor_boi, connection = self.connect_to_database()
        # create SQL INSERT query
        query = """INSERT INTO letterboxd_reviews(movie_id,
                                                  review_date,
                                                  user_rating,
                                                  review_text,
                                                  review_id,
                                                  username)
                                                  VALUES """ + row_insertions + ";"
        # execute query
        cursor_boi.execute(query)
        connection.commit()
        cursor_boi.close()
        connection.close()
        print("Insertion Complete")

    def scrape_finder(self):
        """
        Grabs all the names and urls of all the movies on Netflix.
        Finder.com has all the movies on Netflix on a single page.
        Scrapes them and adds them to the database.
        """
        url = f'https://www.finder.com/netflix-movies'
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        items = soup.find_all(class_='btn-success')
        links = [item['href'] for item in items]
        rows = soup.find_all(scope="row")
        titles = []
        for row in rows:
            if row['data-title'] == 'title':
                titles.append(row.get_text())
        df = pd.DataFrame({'title': titles, 'url': links})
        row_insertions = ""
        for i in list(df.itertuples(index=False)):
            row_insertions += str((i.title, i.url)) + ", "
        row_insertions = row_insertions[:-2]
        cursor_boi, connection = self.connect_to_database()
        query = "INSERT INTO netflix_urls(title, url) VALUES " + row_insertions + ";"
        cursor_boi.execute(query)
        connection.commit()
        cursor_boi.close()
        connection.close()
        print("Insertion Complete")


def checker(str):
    """
    Quick utility function to help with our input Q&A
    """
    valid_inputs = ['y', 'yes', 'n', 'no']
    var = input(str).lower()
    while not var in valid_inputs:
        print("Valid inputs for this question are y, n, yes, and no.")
        var = input(str).lower()
    return var

if __name__ == "__main__":
    start = int(input("Start at which row? "))
    end = int(input("End at which row? (Inclusive)"))
    if start > end:
        raise ValueError("The starting position needs to be less than or \
equal to the end position.")
    max_iter = int(input("Maximum iterations? "))
    if max_iter < 1:
        raise ValueError("Maximum iterations must be positive.")
    scraper_instance = input("Which scraper instance is this? ")
    s = Scraper(start, end, max_iter, scraper_instance)
    website = checker("Are you scraping IMDB?")
    if website == "y" or website == "yes":
        update = checker("Do you want to reject reviews already \
in the database?")
        if update == "y" or update == "yes":
            s.update()
        elif update == "n" or update == "no":
            s.scrape()
    elif website == "n" or website == "no":
        website2 = checker("Are you scraping Letterboxd?")
        if website2 == "y" or website2 == "yes":
            s.scrape_letterboxd()
        elif website2 == "n" or website2 == "no":
            s.scrape_finder()
