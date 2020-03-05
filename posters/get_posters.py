import psycopg2
import pandas as pd
import requests
import os
import re
import sys
import time
from decouple import config
from getpass import getpass
import tmdbsimple as tmdb


class Posters():
    """
    Makes a call to the TMDb API for the poster url.

    Inserts the url and the corresponding IMDbID to the DB.
    """

    def __init__(self):
        self.all_ids = []
        self.max_iter_count = max_iter
        self.database = config("DB_NAME")
        self.user = config("DB_USER")
        self.password = config("DB_PASSWORD")
        self.host = config("DEV")
        self.port = config("PORT")
        self.filename = config("FILENAME")
        self.tmdb.API_KEY = config("tmdbKey")

    def connect_to_database(self):
        """
        Connects to the database.

        Uses class variables set from the environment and takes no
        arguments other than self. Returns a cursor object and a connection
        object.
        """
        connection = psycopg2.connect(
            database = self.database,
            user = self.user,
            password = self.password,
            host = self.host,
            port = self.port
            )
        return connection.cursor(), connection

    def get_ids(self):
        """
        Looks for a csv and converts it to a list of movie ids.

        Takes in the path to a file to read into a dataframe.
        Uses a class variable set from environment variable
        FILENAME to look for a csv which is parsed from the tarbal released
        by IMDb.com which only has the list of MovieIDs for films over 70 minutes
        in length and which are not pornographic.

        """
        df = pd.read_csv(self.filename, encoding = 'ascii', header=None)

        #get all the rows from the second column
        id_list = [row for row in df.iloc[:, 1]]
        self.all_ids = id_list

        return id_list

    def show(self, lst):
        """
        Outputs any list in a string formatted output.
        """
        for count, index in enumerate(lst):
            print(f"{count+1} {index}")

    def make_dataframe(self, movie_id, poster_url):
        """
        Creates a pandas dataframe with the movieID and the URL for the poster.
        """

        df = pd.DataFrame(
            {
                'movie_id' : movie_id,
                'poster_url' : poster_url
                })
        return df

    def api_query(self):
        """
        Queries the TMDb API for movie poster URLs.

        make_dataframe and insert_rows are intended to be used inside
        this function. Takes in the id of the movie in "ttxxxxxxx" format,
        robust to different numbers of numerals.
        """

        id_list = self.get_ids()

        movie_id = []
        poster_url = []
        iteration_counter = 0

        for count, id in enumerate(id_list):
            try:
                None_count = 0
                url_count = 0

                movie_id.append(id)

                result = tmdb.Find('{}'.format(id_list[id])).info(external_source='imdb_id')['movie_results'][0]['poster_path']
            except Exception:
                poster_url.append('None')
                None_count += 1
            while True:
                if iteration_counter >= self.max_iter_count:
                    df = self.make_dataframe(movie_id, poster_url)
                    self.insert_rows(df)
                    movie_id.clear()
                    poster_url.clear()
                    iteration_counter = 0
                    df = df.iloc[0:0]


                movie_id.append(id.replace("tt", ""))
                try:
                    poster_url.append(result)
                    url_count += 1
                    iteration_counter += 1
                    break
                except Exception:
                    poster_url.append('None')
                    None_count += 1
                    iteration_counter += 1
                    break

        df = self.make_dataframe(movie_id, poster_url)
        self.insert_rows(df)
        print("This many posters stored:", url_count)
        print("This many missing posters:", None_count)

    def insert_rows(self, df):
        """
        Connects to the database and inserts poster urls as new rows.
        Takes a dataframe and formats it into a very long string to convert to
        SQL. Connects to the database, executes the query, and closes the cursor
        and connection.
        """

        #convert rows into tuples
        row_insertions = ""
        for in in list(df.intertuples(index=False)):
            row_insertions += str((
                              i.movie_id,
                              i.poster_url)) + ", "

        row_insertions = row_insertions[:-2]
        cursor_obj, connection = self.connect_to_database()
        #create SQL INSERT query
        query = """INSERT INTO reviews(movie_id,
                                    poster_url)
                                    VALUES """ + row_insertions + ";"

        #execute query
        cursor_obj.execute(query)
        connection.commit()
        cursor_obj.close()
        connection.close()
        print("Insertion Complete")

if __name__ == "__main__":
    max_iter = int(input("Maximum iterations? "))
    if max_iter < 1:
        raise ValueError("Maximum iterations must be positive.")