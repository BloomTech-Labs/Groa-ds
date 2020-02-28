from helpers import fill_id, df_to_id_list, prep_data
import os 
import psycopg2
import pandas as pd
import numpy as np
import gensim
from dotenv import load_dotenv
load_dotenv()
import warnings;
warnings.filterwarnings('ignore')

class Recommender(object):

    def __init__(self, model_path):
        """Initialize model with name of .model file"""
        self.model_path = model_path
        self.model = None
        self.id_book = pd.read_csv('exported_data/title_basics_small.csv')

    def connect_db(self):
        """connect to database, create cursor."""
        connection = psycopg2.connect(
            database  = 'postgres',
            user      = 'postgres',
            password  = os.getenv('DB_PASSWORD'),
            host      = os.getenv('DEV'),
            port      = 5432
        )
        # create cursor that is used throughout
        try:
            self.cursor_dog = connection.cursor()
            self.connection = connection  
            print("Connected!")
        except Exception as e:
            print("Connection problem chief!\n")
            print(e)

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

    def _get_info(self, id, score=None):
        """Takes an IMDB movie id string and returns the movie info from the DB"""
        try:
            info_query = f"""
            SELECT m.primary_title, m.start_year, r.average_rating, r.num_votes
            FROM imdb_movies m
            JOIN imdb_ratings r ON m.movie_id = r.movie_id
            WHERE m.movie_id = '{id}'"""
            self.cursor_dog.execute(info_query)
        except Exception as e:
            return tuple([f"Movie title unknown. ID:{id}", None, None, None, None, None, id])

        t = self.cursor_dog.fetchone()
        if t:
            title = tuple([t[0], t[1], f"https://www.imdb.com/title/tt{id}/", t[2], t[3], score, id])
            return title
        else:
            return tuple([f"Movie title not retrieved. ID:{id}", None, None, None, None, None, id])

    def get_most_similar_title(self, id, id_list):
        """Get the title of the most similar movie to id from id_list"""
        clf = self._get_model()
        vocab = clf.wv.vocab
        if id not in vocab:
            return ""
        id_list = [id for id in id_list if id in vocab] # ensure all in vocab
        id_book = self.id_book
        match = clf.wv.most_similar_to_given(id, id_list)
        return id_book['primaryTitle'].loc[id_book['tconst'] == int(match)].values[0]

    def predict(self, input, bad_movies=[], hist_list=[], val_list=[],
                ratings_dict = {}, checked_list=[], rejected_list=[],
                n=50, harshness=1, rec_movies=True,
                show_vibes=False, scoring=False, return_scores=False):
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

        clf = self._get_model()
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

        def _score_model(recs, val_list):
            """Returns the number of recs that were already in the user's watchlist. Validation!"""
            ids = [x[0] for x in recs]
            return len(list(set(ids) & set(val_list)))

        aggregated = _aggregate_vectors(input, checked_list)
        recs = _similar_movies(aggregated, bad_movies, n=n)
        recs = _remove_dupes(recs, input, bad_movies, hist_list, checked_list + rejected_list)
        formatted_recs = [self._get_info(x[0], x[1]) for x in recs]
        if val_list:
            if return_scores:
                return tuple([_score_model(recs, val_list), sum([i[3] for i in formatted_recs if i[3] is not None])/len(formatted_recs)])
            elif scoring:
                print(f"The model recommended {_score_model(recs, val_list)} movies that were on the watchlist!\n")
                print(f"\t\t Average Rating: {sum([i[3] for i in formatted_recs if i[3] is not None])/len(formatted_recs)}\n")
        if show_vibes:
            print("You'll get along with people who like: \n")
            for x in dupes:
                print(self._get_info(x[0], x[1]))
            print('\n')
        if rec_movies:
            return formatted_recs