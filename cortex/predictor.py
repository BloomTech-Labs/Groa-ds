import boto3
import json
from datetime import datetime
import random
import hashlib
import pandas as pd
from recommender import Recommender
from helpers import fill_id, df_to_id_list, prep_data

import warnings;
warnings.filterwarnings('ignore')


class PythonPredictor:
    def __init__(self, config={}):

        self.model = Recommender('models/w2v_limitingfactor_v3.51.model')

        pass

    def predict(self, payload): # recieves userid, outputs recommendation_id

        self.model.connect_db()
        user_id = payload

        """ Check if user id exists """
        query = "SELECT EXISTS(SELECT 1 FROM user_letterboxd_ratings where user_id=%s);"
        self.model.cursor_dog.execute(query, (user_id,))
        boolean_letterboxd = self.model.cursor_dog.fetchall()
        if boolean_letterboxd[0][0]==False:
            print("letterboxd user_id not found")

        query = "SELECT EXISTS(SELECT 1 FROM user_imdb_ratings where user_id=%s);"
        self.model.cursor_dog.execute(query, (user_id,))
        boolean_imdb = self.model.cursor_dog.fetchall()
        if boolean_imdb[0][0]==False:
            print("imdb user_id not found")

        if ((boolean_letterboxd[0][0]==False) & (boolean_imdb[0][0]==False)):
            self.model.cursor_dog.close()
            self.model.connection.close()
            return "Neither IMDB or Letterboxd user_id found"

        """ IMDB data """
        if boolean_imdb[0][0]:
            self.model.cursor_dog.execute("SELECT date, name, year, rating FROM user_imdb_ratings WHERE user_id=%s;", (user_id,))
            ratings_sql= self.model.cursor_dog.fetchall()
            im = pd.DataFrame(ratings_sql, columns = ['Date', 'Name', 'Year', 'Letterboxd URI', 'Rating'])
            drop = ['Your Rating', 'Date Rated', 'Title', 'Const', 'URL', 'Title Type', 'IMDb Rating', 'Runtime (mins)', 'Genres', 'Num Votes', 'Release Date', 'Directors']
            im['Rating'] = im['Your Rating']
            im['Date'] = im['Date Rated']
            im['Name'] = im['Title']
            im = im.drop(columns=drop)

        """ Letterboxd data """
        self.model.cursor_dog.execute("SELECT date, name, year, letterboxd_uri, rating FROM user_letterboxd_ratings WHERE user_id=%s;", (user_id,))
        ratings_sql= self.model.cursor_dog.fetchall()
        ratings = pd.DataFrame(ratings_sql, columns = ['Date', 'Name', 'Year', 'Letterboxd URI', 'Rating'])
        ratings= ratings.dropna()

        self.model.cursor_dog.execute("SELECT date, name, year, letterboxd_uri FROM user_letterboxd_watchlist WHERE user_id=%s;", (user_id,))
        watchlist_sql= self.model.cursor_dog.fetchall()
        watchlist = pd.DataFrame(watchlist_sql, columns = ['Date', 'Name', 'Year', 'Letterboxd URI'])
        watchlist = watchlist.dropna()

        self.model.cursor_dog.execute("SELECT date, name, year, letterboxd_uri FROM user_letterboxd_watched WHERE user_id=%s;", (user_id,))
        watched_sql= self.model.cursor_dog.fetchall()
        watched = pd.DataFrame(watched_sql, columns = ['Date', 'Name', 'Year', 'Letterboxd URI'])
        watched = watched.dropna()

        """ Prepare data  """

        if boolean_imdb[0][0]:
            if len(im) > len(ratings):
                ratings = im

        good_list, bad_list, hist_list, val_list, ratings_dict = prep_data(
                                    ratings, watched_df=None, watchlist_df=None, good_threshold=3, bad_threshold=2)

        """ Run prediction with parameters """

        predictions = self.model.predict(good_list, bad_list, hist_list, val_list, ratings_dict, n=20, harshness=4, rec_movies=True, scoring=True,)

        """ Turn predictions into JSON """

        names = ['Title', 'Year', 'IMDB URL', 'Average Rating', 'Number of Votes', 'Similarity Score', 'IMDB ID']
        names_lists = {key:[] for key in names}

        for x in range(0, len(predictions[0])):
            for y in range(0, len(predictions)):
                names_lists[names[x]].append(predictions[y][x])

        results_dict = [dict(zip(names_lists,t)) for t in zip(*names_lists.values())]
        recommendation_json = json.dumps(results_dict)


        """ Commit to the database """

        string_json = str(recommendation_json)
        hash_object = hashlib.md5(string_json.encode('ascii'))
        recommendation_id = hash_object.hexdigest()

        query = "SELECT EXISTS(SELECT 1 FROM recommendations where recommendation_id=%s);"
        self.model.cursor_dog.execute(query, (recommendation_id,))
        boolean = self.model.cursor_dog.fetchall()
        date = datetime.now()
        model_type = 'Watch history model'

        if boolean[0][0]: # True
            self.model.cursor_dog.close()
            self.model.connection.close()
            return "Already recommended", recommendation_id
        else:
            query = "INSERT INTO recommendations(user_id, recommendation_id, recommendation_json, date, model_type) VALUES (%s, %s, %s, %s, %s);"
            self.model.cursor_dog.execute(query, (user_id, recommendation_id, recommendation_json, date, model_type))
            self.model.connection.commit()
            self.model.cursor_dog.close()
            self.model.connection.close()
            return "Recommendation committed to DB with id:", recommendation_id
