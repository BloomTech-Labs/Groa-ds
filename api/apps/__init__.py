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
import requests
import os
from fastapi import FastAPI

app = FastAPI(
    title="w2v-ratings",
    description="Movie recommendations based on user ratings run through the w2v model",
    version="1.0"
)

def create_app():
    class PythonPredictor:
        def __init__(self):

            

            self.boolean_w2v = True
            self.boolean_r2v = False

        def predict(self, payload): # receives userid, outputs recommendation_id
            boolean_w2v = self.boolean_w2v
            boolean_r2v = self.boolean_r2v

            user_id = payload["user_id"]
            n = payload["number_of_recommendations"]
            good_threshold = payload["good_threshold"]
            bad_threshold = payload["bad_threshold"]
            harshness = payload["harshness"]

            """ connect to database and create cursor """

            connection = psycopg2.connect(
                database  =  os.getenv('DB_NAME'),
                user      =  os.getenv('DB_USER'),
                password  =  os.getenv('DB_PASSWORD'),
                host      =  os.getenv('DEV'),
                port      =  os.getenv('PORT')
            )
            try:
                self.cursor_dog = connection.cursor()
                self.connection = connection
                print("Connected!")
            except Exception as e:
                print("Connection problem chief!\n")
                print(e)

            """ Get id_book from Database"""
            #self.id_book = pd.read_csv('title_basics_small.csv')
            query = "SELECT movie_id, primary_title, original_title, start_year FROM imdb_movies;"
            self.cursor_dog.execute(query)
            movie_sql= self.cursor_dog.fetchall()
            self.id_book = pd.DataFrame(movie_sql, columns = ['tconst', 'primaryTitle', 'originalTitle', 'startYear'])
            self.id_book['startYear'] = self.id_book['startYear'].astype(int)
            self.id_book['tconst'] = self.id_book['tconst'].astype(int)
            self.id_book['primaryTitle'] = self.id_book['primaryTitle'].astype('str')

            """ instantiate the model files and give them this cursor"""

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

            no_rating_data = False
            if ((boolean_letterboxd[0][0]==False) & (boolean_imdb[0][0]==False) & (boolean_groa[0][0]==False)):
                no_rating_data = True
                print("user_id not found in either IMDB, Letterboxd or Groa ratings")

            """ Congregate the ratings data """

            imdb_ratings_df = pd.DataFrame()
            letterboxd_ratings_df = pd.DataFrame()
            groa_ratings_df = pd.DataFrame()

            if boolean_imdb[0][0]:
                query = "SELECT date, name, year, rating FROM user_imdb_ratings WHERE user_id=%s;"
                self.cursor_dog.execute(query, (user_id,))
                ratings_sql= self.cursor_dog.fetchall()
                imdb_ratings_df = pd.DataFrame(ratings_sql, columns = ['Date', 'Name', 'Year', 'Rating'])

            if boolean_letterboxd[0][0]:
                query = "SELECT date, name, year, rating FROM user_letterboxd_ratings WHERE user_id=%s;"
                self.cursor_dog.execute(query, (user_id,))
                ratings_sql= self.cursor_dog.fetchall()
                letterboxd_ratings_df = pd.DataFrame(ratings_sql, columns = ['Date', 'Name', 'Year', 'Rating'])

            if boolean_groa[0][0]:
                query = "SELECT date, name, year, rating FROM user_groa_ratings WHERE user_id=%s;"
                self.cursor_dog.execute(query, (user_id,))
                ratings_sql= self.cursor_dog.fetchall()
                groa_ratings_df = pd.DataFrame(ratings_sql, columns = ['Date', 'Name', 'Year', 'Rating'])

            ratings = pd.concat([imdb_ratings_df, letterboxd_ratings_df, groa_ratings_df]).drop_duplicates()

            """ Check if the user has review data from letterboxd, imdb or groa """
            query = "SELECT EXISTS(SELECT 1 FROM user_letterboxd_reviews where user_id=%s);"
            self.cursor_dog.execute(query, (user_id,))
            boolean_review = self.cursor_dog.fetchall()
            query = "SELECT EXISTS(SELECT 1 FROM user_groa_reviews where user_id=%s);"
            self.cursor_dog.execute(query, (user_id,))
            boolean_groa_review = self.cursor_dog.fetchall()

            no_review_data = False
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
            willnotwatch_sql= self.cursor_dog.fetchall()
            willnotwatchlist_df = pd.DataFrame(willnotwatch_sql, columns = ['Date', 'Name', 'Year'])


            """ Prepare data  """
            good_list, bad_list, hist_list, val_list, ratings_dict = prep_data(
                ratings, self.id_book, self.cursor_dog, watched, watchlist,
                    good_threshold=good_threshold, bad_threshold=bad_threshold)

            """Remove movies if they are in user's willnotwatchlist"""  # this creates null date column
            ratings = pd.merge(ratings, willnotwatchlist_df, how='outer', indicator=True)
            ratings = ratings[ratings['_merge'] == 'left_only'].drop('_merge', axis=1)


            """ Run prediction with parameters then wrangle output """

            w2v_preds = self.w2v.predict(good_list, bad_list, hist_list, val_list, ratings_dict, harshness=harshness, n=n, rec_movies=True, scoring=True,)
            df_w2v = pd.DataFrame(w2v_preds, columns = ['Name', 'Year', 'URL', 'Mean Rating', 'Votes', 'Similarity', 'ID'])



            def get_poster(movie_id):
                query = "SELECT poster_url FROM imdb_movies WHERE movie_id=%s;"
                self.cursor_dog.execute(query, (movie_id,))
                result = self.cursor_dog.fetchall()
                if len(result)==0:
                    return "Not in table"
                if result[0][0] == '':
                    return "No poster"
                else:
                    return result[0][0]

            df_w2v['Gem'] = False
            df_w2v['Poster_URL'] = df_w2v['ID'].apply(get_poster)
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
                both['Poster URL'] = both['ID'].apply(get_poster)
                both = both[['Name', 'Year', 'URL', 'Mean Rating', 'Votes', 'Similarity', 'ID', 'Gem', 'Poster URL']]
                both = both.sample(frac=1, random_state=41).reset_index(drop=True)
                both_list = list(zip(*map(both.get, both)))
                predictions2 = both_list

            """ Turn predictions into JSON """

            def get_JSON(iterable): # receive list of tuples, output JSON
                names = ['Title', 'Year', 'IMDB URL', 'Mean Rating', 'Votes', 'Similarity', 'ID', 'Gem', 'Poster URL']
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
                string_json = str(result) + str(user_id)
                hash_object = hashlib.md5(string_json.encode('ascii'))
                recommendation_id = hash_object.hexdigest()

                query = "SELECT EXISTS(SELECT 1 FROM recommendations where recommendation_id=%s and user_id=%s);"
                self.cursor_dog.execute(query, (recommendation_id, user_id))
                boolean = self.cursor_dog.fetchall()
                date = datetime.now()
                model_type = model_type

                if boolean[0][0]: # True
                        print("Already recommended", recommendation_id, result)
                else:
                    query = """ INSERT INTO recommendations(user_id, recommendation_id, recommendation_json, date, model_type)
                                VALUES (%s, %s, %s, %s, %s);"""
                    self.cursor_dog.execute(query, (user_id, recommendation_id, result, date, model_type))
                    print("Recommendation committed to DB with id:", recommendation_id, result)

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
    def get_user_data(user_id):
        cursor = connection.cursor()
        query = f"SELECT * FROM recommendations WHERE user_id = {user_id};"
        cursor.execute(query)
        recommendations = cursor.fetchall()

        rec_ids = []
        rec_titles = []
        rec_years = []
        rec_ratings = []
        rec_votes = []
        rec_movie_ids = []
        # rec_gems = []
        # dates = []
        genres = []
        # don't think it's needed
        # model_types = []

        for rec in recommendations:
            for unit in rec[2]:
                movie_query = f"SELECT genres FROM imdb_movies WHERE movie_id = '{unit['ID']}';"
                cursor.execute(movie_query)
                movie_data = cursor.fetchone()
                rec_ids.append(rec[1])
                rec_titles.append(unit['Title'])
                rec_years.append(unit['Year'])
                rec_ratings.append(unit['Mean Rating'])
                rec_votes.append(unit['Votes'])
                rec_movie_ids.append(unit['ID'])
                genres.append(movie_data[0])
                # rec_gems.append(unit['Gem'])
                # dates.append(rec[3])
                # model_types.append(rec[4])

        cursor.close()
        data = pd.DataFrame({
            'rec_id': rec_ids,
            'title': rec_titles,
            'year': rec_years,
            'avg_rating': rec_ratings,
            'votes': rec_votes,
            'movie_id': rec_movie_ids,
            'genres': genres
        })
        
        return data
    
    
    @app.route("/stats/decade/{user_id}")
    def get_stats_by_decade(user_id: int):
        data = get_user_data(user_id)
        data["decade"] = data["year"].apply(lambda x: x//10*10)
        first_decade = data["decade"].min()
        last_decade = data["decade"].max()
        decade_to_count = {dec: 0 for dec in range(first_decade, last_decade+1, 10)}
        for dec in data["decade"].values:
            decade_to_count[dec] += 1
        
        return decade_to_count

    @app.route("/", methods=['GET'])
    def helloworld():
        welcome_message = "This is the DS API for Groa"
        return welcome_message

    predictor = PythonPredictor()

    @app.route("/recommendation", methods=['GET', 'POST'])
    def ds_predict():
        payload = request.get_json(force=True)
        result = predictor.predict(payload)
        return result

    return app
