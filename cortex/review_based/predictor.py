import boto3
import json 
from datetime import datetime
import random
import numpy as np
import hashlib
import pandas as pd 
from recommender import *
from review_helpers import *
from helpers import *
import zipfile
import warnings;
warnings.filterwarnings('ignore')


class PythonPredictor:
    def __init__(self, config={}): # configure in cortex.yaml

        with open('values.json', 'r') as values_file:
            values = json.load(values_file)
        self.values = values
        
        """ Comment/Uncomment below this when testing locally/deploying on cortex """
        s3 = boto3.client("s3")
        s3.download_file(config["bucket"], config["key"], "files.zip")
        
        with zipfile.ZipFile('files.zip', 'r') as zip_ref:
            zip_ref.extractall('')

        self.w2v = Recommender('w2v_limitingfactor_v3.51.model')
        self.r2v = r2v_Recommender('r2v_Botanist_v1.1000.5.model')
        pass

    def predict(self, payload): # recieves userid, outputs recommendation_id

        self.w2v.connect_db() # use w2v for queries mostly 
        self.r2v.connect_db() # probably delete this later 
        user_id = payload
        
        """ Check if user id exists """
        query = "SELECT EXISTS(SELECT 1 FROM user_letterboxd_ratings where user_id=%s);" 
        self.w2v.cursor_dog.execute(query, (user_id,))
        boolean_letterboxd = self.w2v.cursor_dog.fetchall()
        if boolean_letterboxd[0][0]==False: 
            print("user_id not found in Letterboxd ratings")
        
        query = "SELECT EXISTS(SELECT 1 FROM user_imdb_ratings where user_id=%s);" 
        self.w2v.cursor_dog.execute(query, (user_id,))
        boolean_imdb = self.w2v.cursor_dog.fetchall()
        if boolean_imdb[0][0]==False: 
            print("user_id not found in IMDB ratings")
            
        if ((boolean_letterboxd[0][0]==False) & (boolean_imdb[0][0]==False)):
            print("user_id not found in either IMDB or Letterboxd ratings")
            
        query = "SELECT EXISTS(SELECT 1 FROM user_letterboxd_reviews where user_id=%s);" 
        self.w2v.cursor_dog.execute(query, (user_id,))
        boolean_review = self.w2v.cursor_dog.fetchall()       
        if boolean_review[0][0]==False: 
            print("user_id not found in Letterboxd reviews")
            
        if ((boolean_letterboxd[0][0]==False) & (boolean_imdb[0][0]==False) * (boolean_review[0][0]==False)):
            self.w2v.connection.close()
            self.r2v.connection.close()
            return "user_id not found in either IMDB or Letterboxd ratings or Letterboxd reviews"
        
        """ IMDB data """
        if boolean_imdb[0][0]:
            self.w2v.cursor_dog.execute("SELECT date, name, year, rating FROM user_imdb_ratings WHERE user_id=%s;", (user_id,))
            ratings_sql= self.w2v.cursor_dog.fetchall()
            im = pd.DataFrame(ratings_sql, columns = ['Date', 'Name', 'Year', 'Letterboxd URI', 'Rating'])
            drop = ['Your Rating', 'Date Rated', 'Title', 'Const', 'URL', 'Title Type', 'IMDb Rating', 'Runtime (mins)', 'Genres', 'Num Votes', 'Release Date', 'Directors']
            im['Rating'] = im['Your Rating']
            im['Date'] = im['Date Rated']
            im['Name'] = im['Title']
            im = im.drop(columns=drop)
    
        """ Letterboxd data """
        self.w2v.cursor_dog.execute("SELECT date, name, year, letterboxd_uri, rating FROM user_letterboxd_ratings WHERE user_id=%s;", (user_id,))
        ratings_sql= self.w2v.cursor_dog.fetchall()
        ratings = pd.DataFrame(ratings_sql, columns = ['Date', 'Name', 'Year', 'Letterboxd URI', 'Rating'])

        self.w2v.cursor_dog.execute("SELECT date, name, year, letterboxd_uri FROM user_letterboxd_watchlist WHERE user_id=%s;", (user_id,))
        watchlist_sql= self.w2v.cursor_dog.fetchall()
        watchlist = pd.DataFrame(watchlist_sql, columns = ['Date', 'Name', 'Year', 'Letterboxd URI'])

        self.w2v.cursor_dog.execute("SELECT date, name, year, letterboxd_uri FROM user_letterboxd_watched WHERE user_id=%s;", (user_id,))
        watched_sql= self.w2v.cursor_dog.fetchall()
        watched = pd.DataFrame(watched_sql, columns = ['Date', 'Name', 'Year', 'Letterboxd URI'])
        
        self.w2v.cursor_dog.execute("SELECT date, name, year, letterboxd_uri, rating, rewatch, review, tags, watched_date FROM user_letterboxd_reviews WHERE user_id=%s;", (user_id,))
        reviews_sql= self.w2v.cursor_dog.fetchall()
        reviews = pd.DataFrame(reviews_sql, columns = ['Date', 'Name', 'Year', 'Letterboxd URI', 'Rating', 'Rewatch', 'Review', 'Tags', 'Watched Date'])
       
        """ Prepare data  """
        
        if boolean_imdb[0][0]:
                ratings = im + ratings
                
        reviews = prep_reviews(reviews)
        
        good_list, bad_list, hist_list, val_list, ratings_dict = prep_data(
                                    ratings, watched, watchlist, good_threshold=3, bad_threshold=2) 
        
        """ Run prediction with parameters """

        w2v_preds = self.w2v.predict(good_list, bad_list, hist_list, val_list, ratings_dict, n=100, harshness=3, rec_movies=True, scoring=True,)
        r2v_preds = self.r2v.predict(reviews, n=10)
        df_w2v = pd.DataFrame(w2v_preds, columns = ['Name', 'Year', 'URL', 'Mean Rating', 'Votes', 'Similarity', 'ID'])
        df_w2v['Gem'] = False
        first = df_w2v
        
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
        
        first_list = list(zip(*map(first.get, first)))
        both_list = list(zip(*map(both.get, both)))
        predictions1 = first_list
        predictions2 = both_list

        
        """ Turn predictions into JSON """
        
        def get_JSON(iterable):
            names = ['Title', 'Year', 'IMDB URL', 'Mean Rating', 'Votes', 'Similarity', 'ID', 'Gem']
            names_lists = {key:[] for key in names}

            for x in range(0, len(iterable[0])):
                for y in range(0, len(iterable)):
                    names_lists[names[x]].append(iterable[y][x])

            results_dict = [dict(zip(names_lists,t)) for t in zip(*names_lists.values())]
            recommendation_json = json.dumps(results_dict)
            return recommendation_json
        
        result1 = get_JSON(predictions1)
        result2 = get_JSON(predictions2)
        

        """ Commit to the database """
        
        def commit_to_database(result, model_type):
            string_json = str(result)
            hash_object = hashlib.md5(string_json.encode('ascii'))
            recommendation_id = hash_object.hexdigest()

            query = "SELECT EXISTS(SELECT 1 FROM recommendations where recommendation_id=%s);" 
            self.w2v.cursor_dog.execute(query, (recommendation_id,))
            boolean = self.w2v.cursor_dog.fetchall()
            date = datetime.now()
            model_type = model_type
            
            if boolean[0][0]: # True
                    print("Already recommended", recommendation_id)
            else:
                query = "INSERT INTO recommendations(user_id, recommendation_id, recommendation_json, date, model_type) VALUES (%s, %s, %s, %s, %s);"
                self.w2v.cursor_dog.execute(query, (user_id, recommendation_id, result, date, model_type))
                print("Recommendation committed to DB with id:", recommendation_id)
                
            return recommendation_id
        
        recommendation_one_id = commit_to_database(result1, 'watch history')
        recommendation_two_id = commit_to_database(result2, 'review history')
        
        self.w2v.connection.commit()
        self.w2v.connection.close()
        self.r2v.connection.close()
        
        return recommendation_one_id, recommendation_two_id