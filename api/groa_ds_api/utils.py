import pandas as pd
import numpy as np
import gensim
import re
import os
import psycopg2
import json
import hashlib
from datetime import datetime
from groa_ds_api.models import *
from elasticsearch import Elasticsearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth


class MovieUtility(object):
    """ Movie utility class that uses a W2V model to recommend movies
    based on the movies a user likes and dislikes """

    def __init__(self, model_path: str):
        """ Initialize model with name of .model file """
        self.model_path = model_path
        self.model = self.__load_model()
        self.connection = self.__get_connection()
        self.id_book = self.__get_id_book()
        self.es = self.__get_es()

    # ------- Start Private Methods -------
    def __get_connection(self):
        return psycopg2.connect(
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            host=os.getenv('HOST'),
            port=os.getenv('PORT')
        )

    def __get_es(self):
        return Elasticsearch(
            hosts=[{'host': os.getenv('ELASTIC'), 'port': 443}],
            http_auth=AWS4Auth(os.getenv('ACCESS_ID'), os.getenv(
                'ACCESS_SECRET'), 'us-east-1', 'es'),
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection
        )

    def __get_cursor(self):
        """ Grabs cursor from self.connection """
        try:
            cursor = self.connection.cursor()
            return cursor
        except:
            self.connection = self.__get_connection()
            return self.connection.cursor()

    def __get_id_book(self):
        """ Gets movie data from database to merge with recommendations """
        cursor_dog = self.__get_cursor()
        query = """
        SELECT movie_id, primary_title, start_year, genres, 
        poster_url, trailer_url, description, average_rating 
        FROM movies;"""
        cursor_dog.execute(query)
        movie_sql = cursor_dog.fetchall()
        id_book = pd.DataFrame(movie_sql, columns=[
                               'movie_id', 'title', 'year', 'genres', 'poster_url',
                               'trailer_url', 'description', 'avg_rating'])
        cursor_dog.close()
        return id_book

    def __load_model(self):
        """ Get the model object for this instance, loading it if it's not already loaded """
        w2v_model = gensim.models.Word2Vec.load(self.model_path)
        # Keep only the normalized vectors.
        # This saves memory but makes the model untrainable (read-only).
        w2v_model.init_sims(replace=True)
        self.model = w2v_model
        return self.model

    def __get_info(self, recs: pd.DataFrame):
        """ Merging recs with id_book to get movie info """
        return pd.merge(recs, self.id_book, how='left', on='movie_id')

    def __get_JSON(self, rec_df: pd.DataFrame):
        """ 
        Turn predictions into JSON
        Callers:
            - get_recommendations
            - get_similar_movies
            - get_movie_list
        """
        rec_json = []

        for i in range(rec_df.shape[0]):
            rec = dict(rec_df.iloc[i].to_dict())
            if 'score' in rec:
                rec['score'] = float(rec['score']) if not isinstance(
                    rec['score'], str) else 0.0
            rec['year'] = int(rec['year']) if not isinstance(
                rec['year'], str) else 0
            rec['genres'] = rec['genres'].split(',')
            rec['avg_rating'] = float(rec['avg_rating']) if not isinstance(
                rec['avg_rating'], str) else 0.0
            rec_json.append(rec)

        return rec_json

    def __prep_data(self, ratings_df: pd.DataFrame,
                    watched_df: pd.DataFrame = None,
                    watchlist_df: pd.DataFrame = None,
                    not_watchlist_df: pd.DataFrame = None,
                    good_threshold: int = 4,
                    bad_threshold: int = 3):
        """
        Converts dataframes to lists of movie_ids.
        Callers:
            - get_recommendations
        """
        try:
            # split according to user rating
            good_df = ratings_df[ratings_df['rating'] >= good_threshold]
            bad_df = ratings_df[ratings_df['rating'] <= bad_threshold]
            neutral_df = ratings_df[(ratings_df['rating'] > bad_threshold) & (
                ratings_df['rating'] < good_threshold)]
            # add not_watchlist to bad_df
            bad_df = pd.concat([bad_df, not_watchlist_df])
            # convert dataframes to lists
            good_list = good_df['movie_id'].to_list()
            bad_list = bad_df['movie_id'].to_list()
            neutral_list = neutral_df['movie_id'].to_list()

        except Exception:
            raise Exception("Error making good, bad and neutral list")

        ratings_dict = pd.Series(
            ratings_df['rating'].values, index=ratings_df['movie_id']).to_dict()

        if watched_df is not None:
            # Construct list of watched movies that aren't rated "good" or "bad"
            hist_list = ratings_df[~ratings_df['movie_id'].isin(
                good_list+bad_list)]['movie_id'].to_list()
        else:
            hist_list = neutral_list

        if watchlist_df is not None:
            # gets list of movies user wants to watch for validation
            val_list = watchlist_df['movie_id'].tolist()
        else:
            val_list = []

        return (good_list, bad_list, hist_list, val_list, ratings_dict)

    def __predict(self, input: list,
                  bad_movies: list = [],
                  hist_list: list = [],
                  val_list: list = [],
                  ratings_dict: dict = {},
                  checked_list: list = [],
                  rejected_list: list = [],
                  n: int = 50,
                  harshness: int = 1):
        """
        Returns a list of recommendations, given a list of movies.
        Callers:
            - get_movie_list
            - get_recommendations
        Returns:
        A list of tuples
            (Movie ID, Similarity score)
        """

        clf = self.model
        # list for storing duplicates for scoring
        dupes = []

        def _aggregate_vectors(movies, feedback_list=[]):
            """ Gets the vector average of a list of movies """
            movie_vec = []
            for i in movies:
                try:
                    # get the vector for each movie
                    m_vec = clf.wv.__getitem__(i)
                    if ratings_dict:
                        try:
                            # get user_rating for each movie
                            r = ratings_dict[i]
                            # Use a polynomial to weight the movie by rating.
                            # This equation is somewhat arbitrary. I just fit a polynomial
                            # to some weights that look good. The effect is to raise
                            # the importance of 1, 2, 9, and 10 star ratings to about 1.8.
                            w = ((r**3)*-0.00143) + ((r**2)*0.0533) + \
                                (r*-0.4695) + 2.1867
                            m_vec = m_vec * w
                        except:
                            continue
                    movie_vec.append(m_vec)
                except KeyError:
                    continue
            if feedback_list:
                for i in feedback_list:
                    try:
                        f_vec = clf.wv.__getitem__(i)
                        # weight feedback by changing multiplier here
                        movie_vec.append(f_vec*1.8)
                    except:
                        continue
            return np.mean(movie_vec, axis=0)

        def _similar_movies(v, n, bad_movies=[]):
            """ Aggregates movies and finds n vectors with highest cosine similarity """
            if bad_movies:
                v = _remove_dislikes(bad_movies, v, harshness=harshness)
            return clf.wv.similar_by_vector(v, topn=n+1)[1:]

        def _remove_dupes(recs, input, bad_movies, hist_list=[], feedback_list=[]):
            """ Remove any recommended IDs that were in the input list """
            all_rated = input + bad_movies + hist_list + feedback_list
            nonlocal dupes
            dupes = [x for x in recs if x[0] in input]
            return [x for x in recs if x[0] not in all_rated]

        def _remove_dislikes(bad_movies, good_movies_vec, rejected_list=[], harshness=1):
            """ Takes a list of movies that the user dislikes.
            Their embeddings are averaged,
            and subtracted from the input. """
            bad_vec = _aggregate_vectors(bad_movies, rejected_list)
            bad_vec = bad_vec / harshness
            return good_movies_vec - bad_vec

        aggregated = _aggregate_vectors(input, checked_list)
        recs = _similar_movies(aggregated, n, bad_movies)
        recs = _remove_dupes(recs, input, bad_movies,
                             hist_list, checked_list + rejected_list)
        return recs

    def __get_list_preview(self, data: tuple):
        """ 
        Turns list preview sql into an object.
        Callers:
            - get_user_lists
            - get_all_lists 
        """
        return {
            "list_id": data[0],
            "name": data[1],
            "private": data[2]
        }

    def __run_query(self, query: str,
                    params: tuple = None,
                    commit: bool = False,
                    fetch: str = "one"):
        try:
            cursor_dog = self.__get_cursor()
            if params is None:
                cursor_dog.execute(query)
            else:
                cursor_dog.execute(query, params)
            result = None
            if fetch == "one":
                result = cursor_dog.fetchone()[0]
            elif fetch == "all":
                result = cursor_dog.fetchall()
            if commit:
                self.connection.commit()
            cursor_dog.close()
            return True, result
        except:
            # refresh connection to avoid FailedTransaction
            self.connection = self.__get_connection()
            return False, None
    # ------- End Private Methods -------

    # ------- Start Public Methods -------
    def add_rating(self, payload: RatingInput):
        query = "SELECT COUNT(*) FROM user_ratings WHERE user_id = %s AND movie_id = %s;"
        params = (payload.user_id, payload.movie_id)
        success, rating = self.__run_query(query, params=params, fetch="one")
        if not success:
            return "Failure"
        if rating > 0:
            query = """UPDATE user_ratings SET rating = %s, date = %s
            WHERE user_id = %s AND movie_id = %s"""
            params = (payload.rating, datetime.now(),
                      payload.user_id, payload.movie_id)
        else:
            query = """
            INSERT INTO user_ratings
            (user_id, movie_id, rating, date, source)
            VALUES (%s, %s, %s, %s, %s)
            """
            params = (payload.user_id, payload.movie_id,
                      payload.rating, datetime.now(), "groa")
        success, _ = self.__run_query(
            query, params=params, commit=True, fetch="none")
        if not success:
            return "Failure"
        return "Success"

    def remove_rating(self, user_id, movie_id):
        """
        Removes a single rating from the user_ratings table.
        """
        query = "DELETE FROM user_ratings WHERE user_id = %s AND movie_id = %s;"
        params = (user_id, movie_id)
        success, _ = self.__run_query(
            query, params=params, commit=True, fetch="none")
        if not success:
            return "Failure"
        return "Success"

    def add_to_watchlist(self, payload: UserAndMovieInput):
        query = "SELECT COUNT(*) FROM user_watchlist WHERE user_id = %s AND movie_id = %s;"
        params = (payload.user_id, payload.movie_id)
        success, watchlist = self.__run_query(
            query, params=params, fetch="one")
        if not success:
            return "Failure"
        if watchlist == 0:
            query = """
            INSERT INTO user_watchlist
            (user_id, movie_id, date, source)
            VALUES (%s, %s, %s, %s);
            """
            params = (payload.user_id, payload.movie_id,
                      datetime.now(), "groa")
            success, _ = self.__run_query(
                query, params=params, commit=True, fetch="none")
            if not success:
                return "Failure"
        return "Success"

    def remove_watchlist(self, user_id, movie_id):
        query = "DELETE FROM user_watchlist WHERE user_id = %s AND movie_id = %s;"
        params = (user_id, movie_id)
        success, _ = self.__run_query(
            query, params=params, commit=True, fetch="none")
        if not success:
            return "Failure"
        return "Success"

    def add_to_notwatchlist(self, payload: UserAndMovieInput):
        query = "SELECT COUNT(*) FROM user_willnotwatchlist WHERE user_id = %s AND movie_id = %s;"
        params = (payload.user_id, payload.movie_id)
        success, notwatchlist = self.__run_query(
            query, params=params, fetch="one")
        if not success:
            return "Failure"
        if notwatchlist == 0:
            query = """
            INSERT INTO user_willnotwatchlist
            (user_id, movie_id, date)
            VALUES (%s, %s, %s);
            """
            params = (payload.user_id, payload.movie_id, datetime.now())
            success, _ = self.__run_query(
                query, params=params, commit=True, fetch="none")
            if not success:
                return "Failure"
        return "Success"

    def remove_notwatchlist(self, user_id, movie_id):
        query = "DELETE FROM user_willnotwatchlist WHERE user_id = %s AND movie_id = %s;"
        success, _ = self.__run_query(
            query,
            params=(user_id, movie_id),
            commit=True,
            fetch="none")
        if not success:
            return "Failure"
        return "Success"

    def search_movies(self, query: str):
        result = self.es.search(index="groa", size=20, expand_wildcards="all", body={
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["description", "primary_title", "original_title", "genres"]
                }
            }
        })
        movie_ids = []
        for elem in result['hits']['hits']:
            movie_ids.append(elem['_id'])
        search_df = self.__get_info(pd.DataFrame({"movie_id": movie_ids}))
        search_df = search_df.fillna("None")
        search_json = self.__get_JSON(search_df)
        return {
            "data": search_json
        }

    def add_interaction(self, user_id: str, movie_id: str):
        query = """
        UPDATE recommendations_movies
        SET interaction = TRUE
        FROM recommendations
        WHERE recommendations.user_id = %s 
        AND recommendations_movies.movie_id = %s;
        """
        params = (user_id, movie_id)
        success, _ = self.__run_query(
            query, params=params, commit=True, fetch="none")
        if not success:
            return "Failure"
        return "Success"

    def create_movie_list(self, payload: CreateListInput):
        """ Creates a MovieList """
        query = """INSERT INTO movie_lists
        (user_id, name, private) VALUES (%s, %s, %s) RETURNING list_id;"""
        params = (payload.user_id, payload.name, payload.private)
        success, list_id = self.__run_query(query, params=params, commit=True)
        if not success:
            return "Failure"
        return {
            "list_id": list_id,
            "name": payload.name,
            "private": payload.private
        }

    def get_movie_list(self, list_id: int):
        """ Gets all movies in MovieList and the associated recs """
        query = """SELECT l.movie_id, m.primary_title, m.start_year, m.genres, m.poster_url 
        FROM list_movies AS l LEFT JOIN movies AS m ON l.movie_id = m.movie_id
        WHERE l.list_id = %s;"""
        success, list_sql = self.__run_query(
            query, params=(list_id,), fetch="all")
        if not success:
            return "Failure"
        list_json = {
            "data": [],
            "recs": []
        }
        if len(list_sql) > 0:
            movie_ids = [movie[0] for movie in list_sql]
            data_df = self.__get_info(pd.DataFrame({"movie_id": movie_ids}))
            data_df = data_df.fillna("None")
            list_json["data"] = self.__get_JSON(data_df)
            w2v_preds = self.__predict(movie_ids)
            df_w2v = pd.DataFrame(w2v_preds, columns=['movie_id', 'score'])
            rec_data = self.__get_info(df_w2v)
            rec_data = rec_data.fillna("None")
            list_json["recs"] = self.__get_JSON(rec_data)
        return list_json

    def get_user_lists(self, user_id: str):
        """ Get user's MovieLists """
        query = "SELECT list_id, name, private FROM movie_lists WHERE user_id = %s;"
        success, user_lists = self.__run_query(
            query, params=(user_id,), fetch="all")
        if not success:
            return "Failure"
        user_lists_json = [self.__get_list_preview(
            elem) for elem in user_lists]
        return user_lists_json

    def get_all_lists(self):
        """ Get all MovieLists """
        query = "SELECT list_id, name, private FROM movie_lists WHERE private=FALSE;"
        success, lists = self.__run_query(query, fetch="all")
        if not success:
            return "Failure"
        lists_json = [self.__get_list_preview(elem) for elem in lists]
        return lists_json

    def add_to_movie_list(self, list_id: int, movie_id: str):
        """ Add movie to a MovieList """
        query = """INSERT INTO list_movies
        (list_id, movie_id) VALUES (%s, %s);"""
        params = (list_id, movie_id)
        success, _ = self.__run_query(
            query, params=params, commit=True, fetch="none")
        if not success:
            return "Failure"
        return "Success"

    def remove_from_movie_list(self, list_id: int, movie_id: str):
        """ Remove movie from a MovieList """
        query = "DELETE FROM list_movies WHERE list_id = %s AND movie_id = %s;"
        params = (list_id, movie_id)
        success, _ = self.__run_query(
            query, params=params, commit=True, fetch="none")
        if not success:
            return "Failure"
        return "Success"

    def delete_movie_list(self, list_id: int):
        """ Delete a MovieList """
        query = "DELETE FROM movie_lists WHERE list_id = %s RETURNING user_id, private;"
        success, result = self.__run_query(
            query, params=(list_id,), commit=True, fetch="all")
        if not success:
            return "Failure"
        return result[0]

    def get_most_similar_title(self, movie_id: str, id_list: list):
        """ Get the title of the most similar movie to movie_id from id_list """
        clf = self.model
        vocab = clf.wv.vocab
        if movie_id not in vocab:
            return ""
        # ensure all in vocab
        id_list = [movie_id for movie_id in id_list if movie_id in vocab]
        match = clf.wv.most_similar_to_given(movie_id, id_list)
        return match

    def get_service_providers(self, movie_id: str):
        """ Get the service providers of a given movie_id """
        cursor_dog = self.__get_cursor()
        query = """
        SELECT m.provider_id, p.name, p.logo_url, m.provider_movie_url, 
        m.presentation_type, m.monetization_type
        FROM movie_providers AS m
        LEFT JOIN providers AS p ON m.provider_id = p.provider_id
        WHERE m.movie_id = %s; 
        """
        cursor_dog.execute(query, (movie_id,))
        prov_sql = cursor_dog.fetchall()
        prov_json = {
            "data": []
        }
        for provider in prov_sql:
            prov_json["data"].append({
                "provider_id": provider[0],
                "name": provider[1],
                "logo": str(provider[2]),
                "link": provider[3],
                "presentation_type": provider[4],
                "monetization_type": provider[5]
            })
        cursor_dog.close()
        return prov_json

    def get_similar_movies(self, payload: SimInput):
        """ Gets movies with highest cosine similarity """
        # request data
        movie_id = payload.movie_id
        n = payload.num_movies
        # get model
        clf = self.model
        try:
            m_vec = clf.wv.__getitem__(movie_id)
            movies_df = pd.DataFrame(clf.wv.similar_by_vector(
                m_vec, topn=n+1)[1:], columns=['movie_id', 'score'])
            result_df = self.__get_info(movies_df)
            result_df = result_df.fillna("None")
            return {
                "data": self.__get_JSON(result_df)
            }
        except:
            return {
                "data": []
            }

    def get_recent_recommendations(self, user_id: str = None):
        """ Grabs the movies of recent recommendations from our API """
        query = """
        SELECT m.movie_id
        FROM recommendations_movies AS m LEFT JOIN recommendations AS r
        ON m.recommendation_id = r.recommendation_id
        ORDER BY r.date DESC
        LIMIT 50;
        """
        success, recs = self.__run_query(query, fetch="all")
        if not success:
            return "Failure"
        recs_df = pd.DataFrame(recs, columns=["movie_id"])
        rec_data = self.__get_info(recs_df)
        rec_data = rec_data.fillna("None")
        rec_json = self.__get_JSON(rec_data)
        explore_lists = []
        if user_id is not None:
            query = """
            SELECT movie_id FROM user_ratings
            WHERE user_id=%s AND rating > 3
            ORDER BY date DESC
            LIMIT 3;
            """
            success, movie_ids = self.__run_query(
                query, params=(user_id,), fetch="all")
            if not success:
                return "Failure"
            if len(movie_ids) > 0:
                explore_lists = [self.get_similar_movies(SimInput(movie_id=elem[0], num_movies=10))
                                 for elem in movie_ids]
            return {
                "data": rec_json,
                "lists": explore_lists
            }
        return {
            "data": rec_json
        }

    def get_recommendations(self, payload: RecInput, background_tasker):
        """ Uses user's ratings to generate recommendations """
        # request data
        user_id = payload.user_id
        n = payload.num_recs
        good_threshold = payload.good_threshold
        bad_threshold = payload.bad_threshold
        harshness = payload.harshness

        # create cursor
        cursor_dog = self.__get_cursor()

        # Check if user has ratings data
        query = "SELECT date, movie_id, rating FROM user_ratings WHERE user_id=%s;"
        cursor_dog.execute(query, (user_id,))
        ratings_sql = cursor_dog.fetchall()
        ratings = pd.DataFrame(ratings_sql, columns=[
                               'date', 'movie_id', 'rating'])
        if ratings.shape[0] == 0:
            cursor_dog.close()
            return {"data": []}

        # Get user watchlist, willnotwatchlist, watched
        query = "SELECT date, movie_id FROM user_watchlist WHERE user_id=%s;"
        cursor_dog.execute(query, (user_id,))
        watchlist_sql = cursor_dog.fetchall()
        watchlist = pd.DataFrame(watchlist_sql, columns=['date', 'movie_id'])

        query = "SELECT date, movie_id FROM user_watched WHERE user_id=%s;"
        cursor_dog.execute(query, (user_id,))
        watched_sql = cursor_dog.fetchall()
        watched = pd.DataFrame(watched_sql, columns=['date', 'movie_id'])

        query = "SELECT date, movie_id FROM user_willnotwatchlist WHERE user_id=%s;"
        cursor_dog.execute(query, (user_id,))
        willnotwatch_sql = cursor_dog.fetchall()
        notwatchlist = pd.DataFrame(
            willnotwatch_sql, columns=['date', 'movie_id'])

        # Prepare data
        good_list, bad_list, hist_list, val_list, ratings_dict = self.__prep_data(
            ratings, watched, watchlist, notwatchlist, good_threshold=good_threshold, bad_threshold=bad_threshold
        )

        # Run prediction with parameters then wrangle output
        w2v_preds = self.__predict(
            good_list, bad_list, hist_list, val_list, ratings_dict, harshness=harshness, n=n)
        df_w2v = pd.DataFrame(w2v_preds, columns=['movie_id', 'score'])

        # get movie info using movie_id
        rec_data = self.__get_info(df_w2v)
        rec_data = rec_data.fillna("None")

        def _commit_to_database(model_recs, user_id, num_recs, good, bad, harsh, cursor_dog):
            """ Commit recommendations to the database """
            date = datetime.now()
            model_type = "ratings"

            create_rec = """
            INSERT INTO recommendations 
            (user_id, date, model_type, num_recs, good_threshold, bad_threshold, harshness) 
            VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING recommendation_id;
            """
            cursor_dog.execute(
                create_rec,
                (user_id, date, model_type, num_recs, good, bad, harsh))
            rec_id = cursor_dog.fetchone()[0]

            create_movie_rec = """
            INSERT INTO recommendations_movies
            (recommendation_id, movie_number, movie_id)
            VALUES (%s, %s, %s);
            """

            for num, movie in enumerate(model_recs):
                cursor_dog.execute(
                    create_movie_rec,
                    (rec_id, num+1, movie['movie_id']))

            self.connection.commit()
            cursor_dog.close()

        rec_json = self.__get_JSON(rec_data)

        # add background task to commit recs to DB
        background_tasker.add_task(
            _commit_to_database,
            rec_json, user_id, n, good_threshold, bad_threshold, harshness, cursor_dog)

        return {
            "data": rec_json
        }
    # ------- End Public Methods -------
