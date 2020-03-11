from w2v_helpers import *
from r2v_helpers import *
import psycopg2
import boto3
import zipfile
import pandas as pd
import numpy as np
import json
import hashlib
from datetime import datetime


"""
    Deploy using Cortex.dev service:
    --------------------------------

    The EKS and Docker based CLI service expects a predictor.py file with a PythonPredictor class with 'config'
    as an argument with a predict function to be called each time there is a 'JSON' post
    request to the endpoint, returning a set of 'predictions'.

    This folder starts at about 50kb and about 200mb are downloaded and unzipped when the class is initiated.

    Credentials for the database and s3 bucket are stored in a values.json file.

    BEFORE pushing to github make sure that "values.json" it deleted or listed in gitignore or on a private repo.
"""

class PythonPredictor:
    def __init__(self, config={}): # in cortex deployment config is detected from cortex.yaml

        """ load secret values for database and s3 bucket"""

        with open('values.json', 'r') as values_file:
            values = json.load(values_file)
        self.values = values

        """ download model files and id book """

        self.boolean_w2v = (config["key"] == "models/w2v.zip")
        self.boolean_r2v = (config["key"] == "models/r2v.zip")

        self.boolean_w2v = open("models/w2v.zip")
        self.boolean_r2v = open("models/r2v.zip")

        if self.boolean_w2v:
            s3 = boto3.client("s3")
            s3.download_file(config["bucket"], config["key"], "w2v.zip")

            with zipfile.ZipFile('w2v.zip', 'r') as zip_ref:
                zip_ref.extractall('')


        if self.boolean_r2v:
            s3 = boto3.client("s3")
            s3.download_file(config["bucket"], config["key"], "r2v.zip")

            with zipfile.ZipFile('r2v.zip', 'r') as zip_ref:
                zip_ref.extractall('')

    def predict(self, payload): # recieves userid, outputs recommendation_id
        boolean_w2v = self.boolean_w2v
        boolean_r2v = self.boolean_r2v

        user_id = payload["user_id"]
        n = payload["number_of_recommendations"]
        good_threshold = payload["good_threshold"]
        bad_threshold = payload["bad_threshold"]
        harshness = payload["harshness"]

        """ connect to database and create cursor """

        connection = psycopg2.connect(
            database  =  self.values['DB_NAME'],
            user      =  self.values['DB_USER'],
            password  =  self.values['DB_PASSWORD'],
            host      =  self.values['DEV'],
            port      =  self.values['PORT']
        )
        try:
            self.cursor_dog = connection.cursor()
            self.connection = connection
            print("Connected!")
        except Exception as e:
            print("Connection problem chief!\n")
            print(e)

        """ instantiate the model files and give them this cursor"""

        self.id_book = pd.read_csv('title_basics_small.csv')

        if boolean_w2v:
            self.w2v = Recommender('w2v_limitingfactor_v2.model', self.id_book, self.cursor_dog)
        if boolean_r2v:
            self.w2v = Recommender('w2v_limitingfactor_v2.model', self.id_book, self.cursor_dog)
            self.r2v = r2v_Recommender('r2v_Botanist_v1.1000.5.model', self.cursor_dog)

        """ Check if user has ratings data in IMDB or Letterboxd or Groa"""

        query = "SELECT EXISTS(SELECT 1 FROM user_letterboxd_ratings where user_id=%s);"
        self.cursor_dog.execute(query, (user_id,))
        boolean_letterboxd = self.cursor_dog.fetchall()
        if boolean_letterboxd[0][0]==False:
            print("user_id not found in Letterboxd ratings")

        query = "SELECT EXISTS(SELECT 1 FROM user_imdb_ratings where user_id=%s);"
        self.cursor_dog.execute(query, (user_id,))
        boolean_imdb = self.cursor_dog.fetchall()
        if boolean_imdb[0][0]==False:
            print("user_id not found in IMDB ratings")

        query = "SELECT EXISTS(SELECT 1 FROM user_groa_ratings where user_id=%s);"
        self.cursor_dog.execute(query, (user_id,))
        boolean_groa = self.cursor_dog.fetchall()
        if boolean_groa[0][0]==False:
            print("user_id not found in Groa ratings")

        if ((boolean_letterboxd[0][0]==False) & (boolean_imdb[0][0]==False) & (boolean_groa[0][0]==False)):
            no_rating_data = True
            print("user_id not found in either IMDB, Letterboxd or Groa ratings")

        """ Congregate the ratings data """

        if boolean_imdb[0][0]:
            query = "SELECT date, name, year, rating FROM user_imdb_ratings WHERE user_id=%s;"
            self.cursor_dog.execute(query, (user_id,))
            ratings_sql= self.cursor_dog.fetchall()
            imdb_ratings_df = pd.DataFrame(ratings_sql, columns = ['Date', 'Name', 'Year', 'Rating'])

        if boolean_letterboxd[0][0]:
            query = "SELECT date, name, year, letterboxd_uri, rating FROM user_letterboxd_ratings WHERE user_id=%s;"
            self.cursor_dog.execute(query, (user_id,))
            ratings_sql= self.cursor_dog.fetchall()
            letterboxd_ratings_df = pd.DataFrame(ratings_sql, columns = ['Date', 'Name', 'Year', 'Letterboxd URI', 'Rating'])

        if boolean_groa[0][0]:
            query = "SELECT date, name, year, rating FROM user_groa_ratings WHERE user_id=%s;"
            self.cursor_dog.execute(query, (user_id,))
            ratings_sql= self.cursor_dog.fetchall()
            groa_ratings_df = pd.DataFrame(ratings_sql, columns = ['Date', 'Name', 'Year', 'Letterboxd URI', 'Rating'])

        ratings = pd.concat([imdb_ratings_df, letterboxd_ratings_df, groa_ratings_df]).drop_duplicates()

        """ Check if the user has review data from letterboxd, imdb or groa """
        query = "SELECT EXISTS(SELECT 1 FROM user_letterboxd_reviews where user_id=%s);"
        self.cursor_dog.execute(query, (user_id,))
        boolean_review = self.cursor_dog.fetchall()
        query = "SELECT EXISTS(SELECT 1 FROM user_groa_reviews where user_id=%s);"
        self.cursor_dog.execute(query, (user_id,))
        boolean_groa_review = self.cursor_dog.fetchall()

        if ((boolean_review[0][0]==False) & (boolean_groa_review[0][0]==False)):
            no_review_data = True
            print("User does not have any review data")

        """ Congregate review data  """

        query = "SELECT date, name, year, letterboxd_uri, rating, rewatch, review, tags, watched_date FROM user_letterboxd_reviews WHERE user_id=%s;"
        self.cursor_dog.execute(query, (user_id,))
        reviews_sql= self.cursor_dog.fetchall()
        letterboxd_reviews = pd.DataFrame(reviews_sql, columns = ['Date', 'Name', 'Year', 'Letterboxd URI', 'Rating', 'Rewatch', 'Review', 'Tags', 'Watched Date'])

        query = "SELECT date, name, year, rating, rewatch, review, tags, watched_date FROM user_groa_reviews WHERE user_id=%s;"
        self.cursor_dog.execute(query, (user_id,))
        reviews_sql= self.cursor_dog.fetchall()
        groa_reviews = pd.DataFrame(reviews_sql, columns = ['Date', 'Name', 'Year', 'Letterboxd URI', 'Rating', 'Rewatch', 'Review', 'Tags', 'Watched Date'])

        reviews = pd.concat([letterboxd_reviews, groa_reviews]).drop_duplicates()

        if boolean_r2v:
            reviews = prep_reviews(reviews)

        """ Check if the user have review or ratings data """

        if ((no_rating_data==True) & (no_review_data==True)):
            self.connection.close()
            return "User does not have ratings or reviews"

        """ Congregate Watchlist """

        query = "SELECT date, name, year, letterboxd_uri FROM user_letterboxd_watchlist WHERE user_id=%s;"
        self.cursor_dog.execute(query, (user_id,))
        watchlist_sql= self.cursor_dog.fetchall()
        letterboxd_watchlist = pd.DataFrame(watchlist_sql, columns = ['Date', 'Name', 'Year', 'Letterboxd URI'])

        query = "SELECT date, name, year FROM user_groa_watchlist WHERE user_id=%s;"
        self.cursor_dog.execute(query, (user_id,))
        watchlist_sql= self.cursor_dog.fetchall()
        groa_watchlist = pd.DataFrame(watchlist_sql, columns = ['Date', 'Name', 'Year'])

        watchlist = pd.concat([letterboxd_watchlist, groa_watchlist]).drop_duplicates()

        query = "SELECT date, name, year, letterboxd_uri FROM user_letterboxd_watched WHERE user_id=%s;"
        self.cursor_dog.execute(query, (user_id,))
        watched_sql= self.cursor_dog.fetchall()
        watched = pd.DataFrame(watched_sql, columns = ['Date', 'Name', 'Year', 'Letterboxd URI'])

        query = "SELECT date, name, year FROM user_groa_willnotwatchlist WHERE user_id=%s;"
        self.cursor_dog.execute(query, (user_id,))
        watched_sql= self.cursor_dog.fetchall()
        willnotwatchlist_df = pd.DataFrame(watched_sql, columns = ['Date', 'Name', 'Year'])


        """ Prepare data  """

        good_list, bad_list, hist_list, val_list, ratings_dict = prep_data(
            ratings, self.id_book, self.cursor_dog, watched, watchlist,
                good_threshold=good_threshold, bad_threshold=bad_threshold)

        """ Run prediction with parameters then wrangle output """

        w2v_preds = self.w2v.predict(good_list, bad_list, hist_list, val_list, ratings_dict, harshness=harshness, n=n, rec_movies=True, scoring=True,)
        df_w2v = pd.DataFrame(w2v_preds, columns = ['Name', 'Year', 'URL', 'Mean Rating', 'Votes', 'Similarity', 'ID'])

        """Remove movies if they are in user's willnotwatchlist"""
        df_w2v = pd.merge(df_w2v, willnotwatchlist_df, indicator=True, how='outer').query('_merge=="left_only"').drop('_merge', axis=1)

        df_w2v['Gem'] = False
        first = df_w2v
        first = first.fillna("None")
        first_list = list(zip(*map(first.get, first)))
        predictions1 = first_list

        if boolean_r2v:
            r2v_preds = self.r2v.predict(reviews, n)
            df_w2v = pd.DataFrame(w2v_preds, columns = ['Name', 'Year', 'URL', 'Mean Rating', 'Votes', 'Similarity', 'ID'])
            cults = pd.DataFrame(r2v_preds[0], columns = ['Name', 'Year', 'URL', 'Votes', 'Mean Rating', 'Rating', 'User', 'Review', 'ID'])
            gems = pd.DataFrame(r2v_preds[1], columns = ['Name', 'Year', 'URL', 'Votes', 'Mean Rating', 'Rating', 'User', 'Review', 'ID'])
            drop = ['User', 'Review', 'Rating']
            df_r2v = pd.concat([cults, gems]).drop(columns=drop)
            df_r2v = df_r2v.drop_duplicates()
            s1 = df_w2v.sort_values(by='Similarity', ascending=False)[:20]
            s1['Gem'] = False
            s2 = df_r2v.sort_values(by='Mean Rating', ascending=False)[:10]
            s2['Gem'] = True
            s2['Similarity'] = 0
            both = pd.concat([s1, s2])
            both = both[['Name', 'Year', 'URL', 'Mean Rating', 'Votes', 'Similarity', 'ID', 'Gem']]
            both = both.sample(frac=1, random_state=41).reset_index(drop=True)
            both_list = list(zip(*map(both.get, both)))
            predictions2 = both_list

        """ Turn predictions into JSON """

        def get_JSON(iterable): # receive list of tuples, output JSON
            names = ['Title', 'Year', 'IMDB URL', 'Mean Rating', 'Votes', 'Similarity', 'ID', 'Gem']
            names_lists = {key:[] for key in names}

            for x in range(0, len(iterable[0])):
                for y in range(0, len(iterable)):
                    names_lists[names[x]].append(iterable[y][x])

            results_dict = [dict(zip(names_lists,t)) for t in zip(*names_lists.values())]
            recommendation_json = json.dumps(results_dict)
            return recommendation_json

        result1 = get_JSON(predictions1)
        if boolean_r2v:
            result2 = get_JSON(predictions2)

        """ Commit to the database """

        def commit_to_database(result, model_type): # receive JSON, commit to database, return recommendation ID
            string_json = str(result)
            hash_object = hashlib.md5(string_json.encode('ascii'))
            recommendation_id = hash_object.hexdigest()

            query = "SELECT EXISTS(SELECT 1 FROM recommendations where recommendation_id=%s and user_id=%s);"
            self.cursor_dog.execute(query, (recommendation_id, user_id))
            boolean = self.cursor_dog.fetchall()
            date = datetime.now()
            model_type = model_type

            if boolean[0][0]: # True
                    print("Already recommended", recommendation_id)
            else:
                query = """ INSERT INTO recommendations(user_id, recommendation_id, recommendation_json, date, model_type)
                            VALUES (%s, %s, %s, %s, %s);"""
                self.cursor_dog.execute(query, (user_id, recommendation_id, result, date, model_type))
                print("Recommendation committed to DB with id:", recommendation_id)

            return recommendation_id

        recommendation1 = commit_to_database(result1, 'ratings model')
        if boolean_r2v:
                recommendation2 = commit_to_database(result2, 'review model')

        self.connection.commit()
        self.connection.close()
        if boolean_w2v:
            return {
                    "recommendation1": recommendation1,
                    "result1": result1
                    }
        if boolean_r2v:
            return {
                    "recommendation1": recommendation1,
                    "result1": result1,
                    "recommendation2": recommendation2,
                    "result2": result2
                    }
