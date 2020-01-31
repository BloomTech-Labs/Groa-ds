import gensim
import numpy as np
import pandas as pd
import psycopg2
import re
import os
import warnings;

warnings.filterwarnings('ignore')


def prep_reviews(df):
    """Converts Letterboxd reviews dataframe to string of concatenated reviews."""
    reviews = ""
    for i in df['Review'].tolist():
        reviews += i
    return reviews.lower()

class r2v_Recommender():
    def __init__(self, model_name):
        """Initialize model with name of .model file"""
        self.model_name = model_name
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
            model_name = self.model_name
            d2v_model = gensim.models.Doc.load(model_name)
            # Keep only the normalized vectors.
            # This saves memory but makes the model untrainable (read-only).
            d2v_model.init_sims(replace=True)
            self.model = d2v_model
        return self.model

    def predict(self, reviews, good_movies, bad_movies=[], hist_list=[],
                n=50, min_dev=1.5, max_votes=1000):
        """Returns a list of recommendations and useful metadata, given a pretrained
        word2vec model and a list of movies.

        Parameters
        ----------

            reviews: string
                String of concatenated user reviews.

            good_movies : iterable
                List of movies that the user likes.

            bad_movies : iterable
                List of movies that the user dislikes.

            hist_list : iterable
                List of movies the user has seen.

            n : int
                Number of recommendations to return.

            min_dev : float, int
                Minimum standard deviation parameter for finding cult movies.
                Higher min_dev --> fewer cult movies returned.

            max_votes : int
                Maximum number of votes for a movie to be considered a hidden gem.

        Returns
        -------
        Two lists of tuples : hidden_gems and cult_movies
            (Title, Year, IMDb URL, Average Rating, Number of Votes, Similarity score)
        """

        clf = self._get_model()
        dupes = []                 # list for storing duplicates

        def _remove_dupes(recs, good_movies, bad_movies):
            """remove any recommended IDs that were in the good_movies list"""
            all_rated = good_movies + bad_movies
            if hist_list:
                all_rated = list(set(all_rated+hist_list))
            nonlocal dupes
            dupes = [x for x in recs if x[0] in all_rated]
            return [x for x in recs if x[0] not in all_rated]

        def similar_users(reviews, n_sims=10):
            """Get similar users based on reviews."""
            aggregated_tokens = aggregate_reviews(review)
            review_tokens = tokenize(aggregated_tokens)
            vec = clf.infer_vector(review_tokens)
            sims = clf.docvecs.most_similar([vec], topn=n_sims)
            return [x[0] for x in sims]

        def hidden_gems(id):
            """TODO: Finds hidden gems."""
            pass

        def cult_movies(sims, min_dev=1.5, n=10):
            """Takes a list of similar users to get cult movies.

            Parameters
            ----------
                sims : list
                    list of similar users.

                min_dev : float, int
                    Minimum number of standard deviations away from mean.
                    Higher number --> fewer results.

                n : max number of results.

            Returns
            -------
            Tuple of recommendations with info.
                (Pmy. Title, Year, Avg. Rating, # Votes, Review, Reviewer, ID)
            """
            simset = set(sims)
            cult_query = f"""
                WITH matches AS (
    						SELECT  m.movie_id mid, m.primary_title tit,
                                    m.start_year start, m.num_votes num,
                                    r.user_rating taste, ra.average_rating avgr,
                                    r.username, r.review_text txt
    						FROM reviews r
    						JOIN movies m ON r.movie_id = m.movie_id
    						JOIN ratings ra ON r.movie_id = ra.movie_id
    						WHERE username IN {simset}
    							AND user_rating BETWEEN 7 AND 10
    						ORDER BY user_rating DESC
    						),
                deviations AS (
        					SELECT  DISTINCT(rr.movie_id) mid,
                                    STDDEV(rev.user_rating) std,
                                    rr.average_rating avgr
        					FROM ratings rr
        					JOIN reviews rev ON rev.movie_id = rr.movie_id
        					GROUP BY rr.movie_id
                            )
                SELECT  matches.tit, matches.start, deviations.avgr,
                        matches.num, matches.txt,  matches.taste, deviations.mid
                FROM deviations
                JOIN matches on matches.mid = deviations.mid
                WHERE matches.taste > (({min_dev} * deviations.std) + deviations.avgr)
                	AND matches.taste < 11
                ORDER BY (matches.taste - deviations.avgr) / deviations.std
                LIMIT {n}"""
            self.cursor_dog.execute(cult_query)
            try:
                cult_recs = self.cursor_dog.fetchall()
            except:
                cult_recs = [("No cult movies found! Better luck next time.",
                                            None, None, None, None, None, None)]
            return cult_recs

        sims = similar_users(reviews, n_sims=30)
        cult_recs = cult_movies(sims, min_dev=min_dev, n=100)
        recs = _remove_dupes(cult_recs, good_movies, bad_movies)
        return recs
