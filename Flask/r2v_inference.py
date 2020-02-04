import gensim
import numpy as np
import pandas as pd
import psycopg2
import re
import os
import warnings;

warnings.filterwarnings('ignore')

"""Review2Vec (R2V) is the second type of model we designed for Groa.
We trained Gensim's Doc2Vec word embedding model on documents containing all the
reviews a user has written on IMDb. Restricting our training data to only those
users who had written at least 6 reviews, we represented almost 60k IMDb users
in this model. R2V can then be used to infer a vector for a new user's movie
reviews, and find "r2v-similar" users. We query those similar users to find cult
movies and hidden gems that the Groa user might enjoy.

Hidden gems are movies are well regarded but relatively underdiscovered. To find
them, we query the database for movies enjoyed by r2v-similar users, having
between 1k and 10k votes.

Cult movies are movies that some users enjoy much more than the average.
Our goal is to provide the user with movies that they might watch and
consider underrated. We query the database for r2v-similar users, and select
movies they rate at least three stars above the average. A lengthier query can
also be found in the SQL directory, which finds movies rated at least 2 standard
deviations above the average, but this query was too slow to be used in the app.
A future team could solve this problem by storing the standard deviation of each
movie's ratings in the movies table."""

def prep_reviews(df):
    """Converts Letterboxd reviews dataframe to list of reviews."""
    reviews = df['Review'].tolist()
    for i in reviews:
        i = i.lower()
    return reviews

class r2v_Recommender():
    def __init__(self, model_path):
        """Initialize model with name of .model file"""
        self.model_path = model_path
        self.model = None
        self.cursor_dog = None

    def connect_db(self):
        """connect to database, create cursor"""
        # connect to database
        connection = psycopg2.connect(
            database  = "postgres",
            user      = "postgres",
            password  = os.getenv('DB_PASSWORD'),
            host      = "movie-rec-scrape.cvslmiksgnix.us-east-1.rds.amazonaws.com",
            port      = '5432'
        )
        # create cursor that is used throughout
        try:
            self.cursor_dog = connection.cursor()
            print("Connected!")
        except:
            print("Connection problem chief!")
        # Enter database password and press Enter.

    def _get_model(self):
        """Get the model object for this instance, loading it if it's not already loaded."""
        if self.model == None:
            model_path = self.model_path
            d2v_model = gensim.models.Doc2Vec.load(model_path)
            # Keep only the normalized vectors.
            # This saves memory but makes the model untrainable (read-only).
            d2v_model.init_sims(replace=True)
            self.model = d2v_model
        return self.model

    def predict(self, reviews, hist_list=[], n=100, max_votes=1000):
        """Returns a list of recommendations and useful metadata, given a pretrained
        word2vec model and a list of movies.

        Parameters
        ----------

            reviews: string
                string of concatenated user reviews.

            hist_list : iterable
                list of movies the user has seen.

            n : int
                number of recommendations to return.

            max_votes : int
                maximum number of votes for a movie to be considered a hidden gem.

        Returns
        -------
        Two lists of tuples: hidden_gems and cult_movies
        (Title, Year, URL, # Votes, Avg. Rating, User Rating, Reviewer, Review, Movie ID)
        """

        clf = self._get_model()

        def _remove_dupes(recs, good_movies, bad_movies):
            """remove any recommended IDs that were in the good_movies list"""
            all_rated = good_movies + bad_movies
            if hist_list:
                all_rated = list(set(all_rated+hist_list))
            dupes = [x for x in recs if x[0] in all_rated]
            return [x for x in recs if x[0] not in all_rated]

        def similar_users(reviews, n_sims=30):
            """Get similar users based on reviews."""
            vec = clf.infer_vector(reviews)
            sims = clf.docvecs.most_similar([vec], topn=n_sims)
            return [x[0] for x in sims]

        def hidden_gems(sims, max_votes=10000, n=10):
            """Finds hidden gems (highly rated but unpopular).

            Parameters
            ----------
                sims : list
                    list of similar users.

                max_votes : int
                    max number of votes (ratings) for movies to be included.

                n : int
                    max number of results.

            Returns
            -------
            List of recommendations as tuples:
            (Title, Year, URL, # Votes, Avg. Rating, User Rating, Reviewer, Review)
            """
            simset = tuple(sims)
            hidden_query = f"""
                            SELECT  m.primary_title, m.start_year, m.movie_id mid,
                                    ra.num_votes num, ra.average_rating avgr,
                                    r.user_rating taste, r.username,
                                    r.review_text txt
                            FROM reviews r
                            JOIN movies m ON r.movie_id = m.movie_id
                            JOIN ratings ra ON r.movie_id = ra.movie_id
                            WHERE username IN {simset}
                            AND user_rating BETWEEN 8 AND 10
								AND ra.average_rating BETWEEN 7 AND 10
								AND ra.num_votes BETWEEN 1000 AND {max_votes}
                            ORDER BY ra.average_rating DESC
                            LIMIT {n}
                            """
            self.cursor_dog.execute(hidden_query)
            try:
                hidden_recs = self.cursor_dog.fetchall()
                hidden_recs = [list(x) for x in hidden_recs]
                for i in hidden_recs:
                    i.append(i[2]) # add ID to the end
                    i[2] = f"https://www.imdb.com/title/tt{i[2]}/" # add URL
                hidden_recs = [tuple(x) for x in hidden_recs]
            except Exception as e:
                print(e)
                hidden_recs = [("No hidden gems found! Better luck next time.",
                                None, None, None, None, None, None, None, None)]
            return hidden_recs

        def cult_movies(sims, n=10):
            """Takes a list of similar users to get cult movies (considered
                underrated by similar users).

            Parameters
            ----------
                sims : list
                    list of similar users.

                n : int
                    max number of results.

            Returns
            -------
            List of recommendations as tuples:
            (Title, Year, URL, # Votes, Avg. Rating, User Rating, Reviewer, Review)
            """
            simset = tuple(sims)
            cult_query = f"""
                            SELECT  m.primary_title, m.start_year, m.movie_id mid,
                                    ra.num_votes num, ra.average_rating avgr,
                                    r.user_rating taste, r.username,
                                    r.review_text txt
                            FROM reviews r
                            JOIN movies m ON r.movie_id = m.movie_id
                            JOIN ratings ra ON r.movie_id = ra.movie_id
                            WHERE username IN {simset}
                            AND user_rating BETWEEN 7 AND 10
								AND user_rating BETWEEN 6 AND 10
								AND user_rating >= (ra.average_rating + 3)
                            ORDER BY user_rating DESC
                            LIMIT {n}
                """
            self.cursor_dog.execute(cult_query)
            try:
                cult_recs = self.cursor_dog.fetchall()
                cult_recs = [list(x) for x in cult_recs]
                for i in cult_recs:
                    i.append(i[2]) # add ID to the end
                    i[2] = f"https://www.imdb.com/title/tt{i[2]}/" # add URL
                cult_recs = [tuple(x) for x in cult_recs]
            except Exception as e:
                print(e)
                cult_recs = [("No cult movies found! Better luck next time.",
                                None, None, None, None, None, None, None, None)]
            return cult_recs

        sims = similar_users(reviews, n_sims=100)
        cult_recs = cult_movies(sims, n=n/2)
        hidden_gems = hidden_gems(sims, n=n/2)
        return [cult_recs, hidden_gems]
