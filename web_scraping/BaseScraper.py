import os
from random import randint
import re
import sys
from datetime import timedelta, datetime
import time

from bs4 import BeautifulSoup # 4.8.2
from decouple import config # 3.3
import pandas as pd # 0.25.0
import psycopg2 # 2.8.4
import requests # 2.22.0
# python 3.7.5

class BaseScraper:
    """
    Scrapes IMDB, Letterboxd, and finder.

    Start and end parameters are inclusive. max_iter controls how
    many loops can be run before the program inserts into the
    database. This indirectly controls the size and frequency of
    insertions. 
    Necessary environment variables are PASSWORD, HOST, PORT,
    and FILENAME.
    """

    def __init__(self, start, end, max_iter):
        self.start = start
        self.end = end + 1
        self.current_ids = []
        self.all_ids = []
        self.range = 0
        self.pickup = 0
        self.max_iter_count = max_iter
        self.scraper_instance = str(randint(2**31, 2**32))
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
