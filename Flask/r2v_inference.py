import gensim
import numpy as np
import pandas as pd
import psycopg2
import re
import os
import warnings;

warnings.filterwarnings('ignore')

cursor_dog = None

def prep_reviews(df):
    """Converts Letterboxd reviews dataframe to list of tokens."""
    reviews_list = df['Review'].tolist()
    return reviews_list

class r2v_Recommender():
    def __init__(self, model_name):
        """Initialize model with name of .model file"""
        self.model_name = model_name
        self.model = None

    def connect_db(self):
        """connect to database, create cursor"""
        # connect to database
        connection = psycopg2.connect(
            database  = "postgres",
            user      = "postgres",
            password  = os.getenv('DB_PASSWORD'),
            host      = "groalives.cvslmiksgnix.us-east-1.rds.amazonaws.com",
            port      = '5432'
        )
        # create cursor that is used throughout
        global cursor_dog
        try:
            cursor_dog = connection.cursor()
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

    def predict(self, reviews, good_movies, bad_movies=[], hist_list=[], val_list=[],
                n=50, harshness=1, rec_movies=True,
                show_vibes=False, scoring=False):
        """Returns a list of recommendations and useful metadata, given a pretrained
        word2vec model and a list of movies.

        Parameters
        ----------

            good_movies : iterable
                List of movies that the user likes.

            bad_movies : iterable
                List of movies that the user dislikes.

            hist_list : iterable
                List of movies the user has seen.

            val_list : iterable
                List of movies the user has already indicated interest in.

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

            scoring : boolean
                If True, prints out the validation score.

        Returns
        -------
        A list of tuples
            (Title, Year, IMDb URL, Average Rating, Number of Votes, Similarity score)
        """

        clf = self._get_model()
        dupes = []                 # list for storing duplicates

        def _aggregate_vectors(movies):
            """Gets the vector average of a list of movies."""
            movie_vec = []
            for i in movies:
                try:
                    movie_vec.append(clf[i])        # get the vector for each movie
                except KeyError:
                    continue
            return np.mean(movie_vec, axis=0)

        def _similar_movies(v, bad_movies=[], n=50):
            """Aggregates movies and finds n vectors with highest cosine similarity."""
            if bad_movies:
                v = _remove_dislikes(bad_movies, v, good_movies=good_movies, harshness=harshness)
            return clf.similar_by_vector(v, topn= n+1)[1:]

        def _remove_dupes(recs, good_movies, bad_movies):
            """remove any recommended IDs that were in the good_movies list"""
            all_rated = good_movies + bad_movies
            if hist_list:
                all_rated = list(set(all_rated+hist_list))
            nonlocal dupes
            dupes = [x for x in recs if x[0] in all_rated]
            return [x for x in recs if x[0] not in all_rated]

        def _get_info(id):
            """Takes an id string and returns the movie info with a url."""
            try:
                cursor_dog.execute(f"""
                select m.primary_title, m.start_year, r.average_rating, r.num_votes
                from movies m
                join ratings r on m.movie_id = r.movie_id
                where m.movie_id = '{id[0]}'""")
            except:
                return tuple([f"Movie title unknown. ID:{id[0]}", None, None, None, None, None])

            t = cursor_dog.fetchone()
            if t:
                title = tuple([t[0], t[1], f"https://www.imdb.com/title/tt{id[0]}/", t[2], t[3], id[1]])
                return title
            else:
                return tuple([f"Movie title unknown. ID:{id[0]}", None, None, None, None, None])

        def _remove_dislikes(bad_movies, good_movies_vec, input=1, harshness=1):
            """Takes a list of movies that the user dislikes.
            Their embeddings are averaged,
            and subtracted from the good_movies."""
            bad_vec = _aggregate_vectors(bad_movies)
            bad_vec = bad_vec / harshness
            return good_movies_vec - bad_vec

        def _score_model(recs, val_list):
            ids = [x[0] for x in recs]
            return len(list(set(ids) & set(val_list)))

        aggregated = _aggregate_vectors(good_movies)
        recs = _similar_movies(aggregated, bad_movies, n=n)
        recs = _remove_dupes(recs, good_movies, bad_movies)
        formatted_recs = [_get_info(x) for x in recs]
        if scoring and val_list:
            print(f"The model recommended {_score_model(recs, val_list)} movies that were on the watchlist!\n")
            print(f"\t\t Average Rating: {sum([i[3] for i in formatted_recs if i[3] is not None])/len(formatted_recs)}\n")
        if show_vibes:
            print("You'll get along with people who like: \n")
            for x in dupes:
                print(_get_info(x))
            print('\n')
        if rec_movies:
            return formatted_recs


test_review = [tuple([x, '']) for x in test_review]
test_aggregated_tokens = aggregate_reviews(test_review)
test_tokens = tokenize(test_aggregated_tokens)
test_vec = model.infer_vector(test_tokens)
results = model.docvecs.most_similar([test_vec], topn= 10)
print("most similar users: \n", results)
