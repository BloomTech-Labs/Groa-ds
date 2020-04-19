import pandas as pd
import numpy as np
import gensim
import re
import os 
import psycopg2
import json
import hashlib
from datetime import datetime


class Recommender(object):

    def __init__(self, model_path):
        """Initialize model with name of .model file"""
        self.model_path = model_path
        # think this only will ever need to be called once
        # probably can remove _get_model
        self.model = self._load_model()
        # self.connection = psycopg2.connect(
        #     database  =  os.getenv('DB_NAME'),
        #     user      =  os.getenv('DB_USER'),
        #     password  =  os.getenv('DB_PASSWORD'),
        #     host      =  os.getenv('DEV'),
        #     port      =  os.getenv('PORT')
        # )
        self.connection = psycopg2.connect(
            database  =  os.getenv('DB_NAME'),
            user      =  os.getenv('DB_USER'),
            password  =  os.getenv('DB_PASSWORD'),
            host      =  os.getenv('HOST'),
            port      =  os.getenv('PORT')
        )
        self.cursor_dog = self.connection.cursor()
        self.id_book = self.get_id_book()
        """
        when should the cursor be instantiated and where will it be closed?
        """
    
    def get_cursor(self):
        try:
            cursor = self.conneciton.cursor()
            return cursor 
        except:
            # self.connection = psycopg2.connect(
            #     database  =  os.getenv('old_DB_NAME'),
            #     user      =  os.getenv('old_DB_USER'),
            #     password  =  os.getenv('old_DB_PASSWORD'),
            #     host      =  os.getenv('DEV'),
            #     port      =  os.getenv('PORT')
            # )
            self.connection = psycopg2.connect(
                database  =  os.getenv('DB_NAME'),
                user      =  os.getenv('DB_USER'),
                password  =  os.getenv('DB_PASSWORD'),
                host      =  os.getenv('HOST'),
                port      =  os.getenv('PORT')
            )
            return self.connection.cursor()
    
    def get_id_book(self):
        """ 
        Get id_book from Database
        this was in get_recommendations method but because it's constant and
        the same for each execution there is no need to fetch and build each time
        """
        # just add poster_path to this to avoid an additional query
        query = "SELECT movie_id, primary_title, start_year, genres, poster_url FROM movies;"
        self.cursor_dog.execute(query)
        movie_sql= self.cursor_dog.fetchall()
        id_book = pd.DataFrame(movie_sql, columns = ['movie_id', 'title', 'year', 'genres', 'poster_url'])
        return id_book

    def _get_model(self):
        """Get the model object for this instance, loading it if it's not already loaded."""
        if self.model == None:
            model_path = self.model_path
            w2v_model = gensim.models.Word2Vec.load(model_path)
            # Keep only the normalized vectors.
            # This saves memory but makes the model untrainable (read-only).
            w2v_model.init_sims(replace=True)
            self.model = w2v_model
        return self.model
    
    def _load_model(self):
        """Get the model object for this instance, loading it if it's not already loaded."""
        w2v_model = gensim.models.Word2Vec.load(self.model_path)
        # Keep only the normalized vectors.
        # This saves memory but makes the model untrainable (read-only).
        w2v_model.init_sims(replace=True)
        self.model = w2v_model
        return self.model

    def _get_info(self, recs):
        """ Merging recs with id_book to get movie info """
        return pd.merge(recs, self.id_book, how='left', on='movie_id')

    def get_most_similar_title(self, id, id_list):
        """Get the title of the most similar movie to id from id_list"""
        clf = self.model
        vocab = clf.wv.vocab
        if id not in vocab:
            return ""
        id_list = [id for id in id_list if id in vocab] # ensure all in vocab
        id_book = self.id_book
        match = clf.wv.most_similar_to_given(id, id_list)
        return match

    def predict(self, input, bad_movies=[], hist_list=[], val_list=[],
                ratings_dict = {}, checked_list=[], rejected_list=[],
                n=50, harshness=1):
        """Returns a list of recommendations and useful metadata, given a pretrained
        word2vec model and a list of movies.

        Parameters
        ----------

            input : iterable
                List of movies that the user likes.

            bad_movies : iterable
                List of movies that the user dislikes.

            hist_list : iterable
                List of movies the user has seen.

            val_list : iterable
                List of movies the user has already indicated interest in.
                Example: https://letterboxd.com/tabula_rasta/watchlist/
                People really load these up over the years, and so they make for
                the best validation set we can ask for with current resources.

            ratings_dict : dictionary
                Dictionary of movie_id keys, user rating values.

            checked_list : iterable
                List of movies the user likes on the feedback form.

            rejected_list : iterable
                List of movies the user dislikes on the feedback form.

            n : int
                Number of recommendations to return.

            harshness : int
                Weighting to apply to disliked movies.
                Ex:
                    1 - most strongly account for disliked movies.
                    3 - divide "disliked movies" vector by 3.

            rec_movies : boolean
                If False, doesn't return movie recommendations (used for scoring).

            show_vibes : boolean
                If True, prints out the dupes as a feature.
                These movies are closest to the user's taste vector,
                indicating some combination of importance and popularity.

            scoring : boolean
                If True, prints out the validation score.

            return_scores : boolean
                If True, skips printing out

        Returns
        -------
        A list of tuples
            (Title, Year, IMDb URL, Average Rating, Number of Votes, Similarity score)
        """

        clf = self.model
        dupes = []                 # list for storing duplicates for scoring

        def _aggregate_vectors(movies, feedback_list=[]):
            """Gets the vector average of a list of movies."""
            movie_vec = []
            for i in movies:
                try:
                    m_vec = clf[i]  # get the vector for each movie
                    if ratings_dict:
                        try:
                            r = ratings_dict[i] # get user_rating for each movie
                            # Use a polynomial to weight the movie by rating.
                            # This equation is somewhat arbitrary. I just fit a polynomial
                            # to some weights that look good. The effect is to raise
                            # the importance of 1, 2, 9, and 10 star ratings to about 1.8.
                            w = ((r**3)*-0.00143) + ((r**2)*0.0533) + (r*-0.4695) + 2.1867
                            m_vec = m_vec * w
                        except KeyError:
                            continue
                    movie_vec.append(m_vec)
                except KeyError:
                    continue
            if feedback_list:
                for i in feedback_list:
                    try:
                        f_vec = clf[i]
                        movie_vec.append(f_vec*1.8) # weight feedback by changing multiplier here
                    except KeyError:
                        continue
            return np.mean(movie_vec, axis=0)

        def _similar_movies(v, bad_movies=[], n=50):
            """Aggregates movies and finds n vectors with highest cosine similarity."""
            if bad_movies:
                v = _remove_dislikes(bad_movies, v, harshness=harshness)
            return clf.similar_by_vector(v, topn= n+1)[1:]

        def _remove_dupes(recs, input, bad_movies, hist_list=[], feedback_list=[]):
            """remove any recommended IDs that were in the input list"""
            all_rated = input + bad_movies + hist_list + feedback_list
            nonlocal dupes
            dupes = [x for x in recs if x[0] in input]
            return [x for x in recs if x[0] not in all_rated]

        def _remove_dislikes(bad_movies, good_movies_vec, rejected_list=[], harshness=1):
            """Takes a list of movies that the user dislikes.
            Their embeddings are averaged,
            and subtracted from the input."""
            bad_vec = _aggregate_vectors(bad_movies, rejected_list)
            bad_vec = bad_vec / harshness
            return good_movies_vec - bad_vec

        aggregated = _aggregate_vectors(input, checked_list)
        recs = _similar_movies(aggregated, bad_movies, n=n)
        recs = _remove_dupes(recs, input, bad_movies, hist_list, checked_list + rejected_list)
        return recs
    
    def get_recommendations(self, payload):
        # request data 
        user_id = payload.user_id
        n = payload.number_of_recommendations
        good_threshold = payload.good_threshold
        bad_threshold = payload.bad_threshold
        harshness = payload.harshness

        """ create cursor """
        try:
            self.cursor_dog = self.get_cursor()
            print("Connected!")
        except Exception as e:
            print("Connection problem chief!\n")
            print(e)

        """ Check if user has ratings data """

        query = "SELECT date, movie_id, rating FROM user_ratings WHERE user_id=%s;"
        self.cursor_dog.execute(query, (user_id,))
        ratings_sql= self.cursor_dog.fetchall()

        ratings = pd.DataFrame(ratings_sql, columns = ['date', 'movie_id', 'rating'])

        """ Are there any ratings from the user? """

        if ratings.shape[0] == 0:
            self.cursor_dog.close()
            return "User does not have ratings"

        print("Got user ratings...")

        """ Get user watchlist, willnotwatchlist, watched """

        query = "SELECT date, movie_id FROM user_watchlist WHERE user_id=%s;"
        self.cursor_dog.execute(query, (user_id,))
        watchlist_sql= self.cursor_dog.fetchall()
        watchlist = pd.DataFrame(watchlist_sql, columns = ['date', 'movie_id'])

        query = "SELECT date, movie_id FROM user_watched WHERE user_id=%s;"
        self.cursor_dog.execute(query, (user_id,))
        watched_sql= self.cursor_dog.fetchall()
        watched = pd.DataFrame(watched_sql, columns = ['date', 'movie_id'])

        query = "SELECT date, movie_id FROM user_willnotwatchlist WHERE user_id=%s;"
        self.cursor_dog.execute(query, (user_id,))
        willnotwatch_sql= self.cursor_dog.fetchall()
        willnotwatchlist_df = pd.DataFrame(willnotwatch_sql, columns = ['date', 'movie_id'])

        print("Got user watchlists, prepping data...")

        """ Prepare data  """
        good_list, bad_list, hist_list, val_list, ratings_dict = prep_data(
            ratings, watched, watchlist, good_threshold=good_threshold, bad_threshold=bad_threshold
            )

        """Remove movies if they are in user's willnotwatchlist"""  # this creates null date column
        # is this needed?? would we want to remove movies user doesn't like when the rating is bad?
        # that is info we could use for recommendations
        # ratings = pd.merge(ratings, willnotwatchlist_df, how='outer', indicator=True)
        # ratings = ratings[ratings['_merge'] == 'left_only'].drop('_merge', axis=1)


        """ Run prediction with parameters then wrangle output """
        print("Getting predictions...")
        w2v_preds = self.predict(good_list, bad_list, hist_list, val_list, ratings_dict, harshness=harshness, n=n)
        df_w2v = pd.DataFrame(w2v_preds, columns=['movie_id', 'score'])
        # get movie info using movie_id
        rec_data = self._get_info(df_w2v)
        rec_data = rec_data.fillna("None")

        """ Turn predictions into JSON """
        def get_JSON(rec_df): # receive list of tuples, output JSON
            names = rec_df.columns
            rec_json = []

            for i in range(rec_df.shape[0]):
                curr_object = dict(rec_df.iloc[i].to_dict())
                rec_json.append({
                    'movie_id': curr_object['movie_id'], 
                    'score': float(curr_object['score']), 
                    'title': curr_object['title'],
                    'year': int(curr_object['year']),
                    'genres': curr_object['genres'].split(','), 
                    'poster_url': curr_object['poster_url']
                    })

            return rec_json

        print("Getting JSON response...")
        rec_json = get_JSON(rec_data)

        """ Commit to the database """
        # need to update to make a row per movie recommended
        def commit_to_database(result, model_type): 
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

        print(f"Sending response with {len(rec_json)} recommendations...")
        # should give response and thread this off somehow
        # recommendation_id = commit_to_database(rec_json, 'ratings model')
        # self.connection.commit()
        return {
                "recommendation_id": 'in test mode',
                "data": rec_json
                }


def prep_data(ratings_df, watched_df=None, watchlist_df=None, good_threshold=4, bad_threshold=3):
    """Converts dataframes of exported Letterboxd data to lists of movie_ids.

    Parameters
    ----------
    ratings_df : pd dataframe
        Letterboxd ratings.

    watched_df : pd dataframe
        Letterboxd watch history.

    watchlist_df : pd dataframe
        Letterboxd list of movies the user wants to watch.
        Used in val_list for scoring the model's performance.

    good_threshold : int
        Minimum star rating (10pt scale) for a movie to be considered "enjoyed" by the user.

    bad_threshold : int
        Maximum star rating (10pt scale) for a movie to be considered "disliked" by the user.


    Returns
    -------
    tuple of lists of ids.
        (good_list, bad_list, hist_list, val_list)
    """
    # what scale is the ratings in?
    # good_list is ratings greater than good_threashold
    # bad_list is ratings below bad_threshold
    # neutral_list is movies not in good or bad list
    # val_list is just movies in watched_df
    # hist_list seems to be movies not in good or bad too?
    # ratings_dict all ids mapped to their ratings
    try:
        # shouldn't be necessary to check for nulls
        # drop rows with nulls in the columns we use
        ratings_df = ratings_df.dropna(axis=0, subset=['rating', 'movie_id'])

        # split according to user rating
        good_df = ratings_df[ratings_df['rating'] >= good_threshold]
        bad_df = ratings_df[ratings_df['rating'] <= bad_threshold]
        neutral_df = ratings_df[(ratings_df['rating'] > bad_threshold) & (ratings_df['rating'] < good_threshold)]
        # split according to user rating (doubled thresholds)
        # good_df = ratings_df[ratings_df['Your Rating'] >= good_threshold*2]
        # bad_df = ratings_df[ratings_df['Your Rating'] <= bad_threshold*2]
        # neutral_df = ratings_df[(ratings_df['Your Rating'] > bad_threshold*2) & (ratings_df['Your Rating'] < good_threshold*2)]
        
        # convert dataframes to lists
        good_list = good_df['movie_id'].to_list()
        bad_list = bad_df['movie_id'].to_list()
        neutral_list = neutral_df['movie_id'].to_list()

    except Exception as e:
        print("Error making good, bad and neutral list")
        raise Exception(e)


    ratings_dict = pd.Series(ratings_df['rating'].values,index=ratings_df['movie_id']).to_dict()

    if watched_df is not None:
        # Construct list of watched movies that aren't rated "good" or "bad"
        hist_list = ratings_df[~ratings_df['movie_id'].isin(good_list+bad_list)]['movie_id'].to_list()
    else: hist_list = neutral_list

    if watchlist_df is not None:
        val_list = watchlist_df['movie_id'].tolist()
    else: val_list = []

    return (good_list, bad_list, hist_list, val_list, ratings_dict)
