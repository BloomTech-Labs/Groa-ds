import gensim
import numpy as np
import pandas as pd
import psycopg2
from decouple import config

def connect_db():
    """connect to database, create cursor"""
    # connect to database
    connection = psycopg2.connect(
        database  = "postgres",
        user      = "postgres",
        password  = config('DB_PASSWORD'),
        host      = "movie-rec-scrape.cvslmiksgnix.us-east-1.rds.amazonaws.com",
        port      = '5432'
    )
    # create cursor that is used throughout
    try:
        c = connection.cursor()
        print("Connected!")
    except:
        print("Connection problem chief!")
    # Enter database password and press Enter.

def df_to_id_list(df):
        """Converts dataframe of movies to a list of the IDs for those movies,
        ready for inferencing."""

        ids = []
        names = df.Name.tolist()
        years = [int(year) for year in df.Year.tolist()]
        info = list(zip(names, years))
        for i, j in info:
            i = i.replace("'", "''")
            try:
                c.execute(f"""
                    SELECT movie_id
                    FROM movies
                    WHERE primary_title ILIKE '{i}' AND start_year = {j}
                    ORDER BY runtime_minutes DESC
                    LIMIT 1""")
                id = c.fetchone()[0]
                ids.append(id)
            except TypeError:
                c.execute(f"""
                    SELECT movie_id,
                        levenshtein(upper('{i}'),
                        UPPER(primary_title)) as distance
                    /* activate levenshtein function in your database with this query:
                        "CREATE extension fuzzystrmatch"
                        Only has to be done once.*/
                    FROM movies
                    ORDER BY distance ASC
                    LIMIT 1
                """)
                id = c.fetchone()[0]
                ids.append(id)
            except:
                continue
        return ids

def prep_data(ratings_df, watched_df=None, watchlist_df=None,
                   good_threshold=4, bad_threshold=3):
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
        try:
            ratings_df = ratings_df.dropna(axis=0, subset=['Rating', 'Name', 'Year'])
            good_df = ratings_df[ratings_df['Rating'] >= good_threshold]
            bad_df = ratings_df[ratings_df['Rating'] <= bad_threshold]
        except Exception as e:
            raise Exception(e)

        good_list = df_to_id_list(good_df)
        bad_list = df_to_id_list(bad_df)

        if watched_df is not None:
            # This will be used to prevent repeat queries when constructing hist_list
            rated_names = good_df.Name.tolist() + bad_df.Name.tolist()
            full_history = watched_df.dropna(axis=0, subset=['Name', 'Year'])
            hist_list = df_to_id_list(full_history[~full_history['Name'].isin(rated_names)])
        else: hist_list = []

        if watchlist_df is not None:
            watchlist_df = watchlist_df.dropna(axis=0, subset=['Name', 'Year'])
            val_list = df_to_id_list(watchlist_df)
        else: val_list = []

        return (good_list, bad_list, hist_list, val_list)

class Recommender(object):

    def __init__(self, model_name):
        """Initialize model with name of .model file"""
        self.model_name = model_name
        self.model = None

    def _get_model(self):
        """Get the model object for this instance, loading it if it's not already loaded."""
        if self.model == None:
            model_name = self.model_name
            print(model_name)
            w2v_model = gensim.models.Word2Vec.load(model_name)
            # Keep only the normalized vectors.
            # This saves memory but makes the model untrainable (read-only).
            w2v_model.init_sims(replace=True)
            self.model = w2v_model
        return self.model

    def predict(self, input, bad_movies=[], hist_list=[], val_list=[],
                n=50, harshness=1, rec_movies=True,
                show_vibes=False, scoring=False):
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
                v = _remove_dislikes(bad_movies, v, input=input, harshness=harshness)
            return clf.similar_by_vector(v, topn= n+1)[1:]

        def _remove_dupes(recs, input, bad_movies):
            """remove any recommended IDs that were in the input list"""
            all_seen = input + bad_movies
            if hist_list:
                all_seen = list(set(all_seen+hist_list))
            nonlocal dupes
            dupes = [x for x in recs if x[0] in all_seen]
            return [x for x in recs if x[0] not in all_seen]

        def _get_info(id):
            """Takes an id string and returns the movie info with a url."""
            try:
                c.execute(f"""
                select m.primary_title, m.start_year, r.average_rating, r.num_votes
                from movies m
                join ratings r on m.movie_id = r.movie_id
                where m.movie_id = '{id[0]}'""")
            except:
                return tuple([f"Movie title unknown. ID:{id[0]}", None, None, None, None, None])

            t = c.fetchone()
            if t:
                title = tuple([t[0], t[1], f"https://www.imdb.com/title/tt{id[0]}/", t[2], t[3], id[1]])
                return title
            else:
                return tuple([f"Movie title unknown. ID:{id[0]}", None, None, None, None, None])


        def _remove_dislikes(bad_movies, good_movies_vec, input=1, harshness=1):
            """Takes a list of movies that the user dislikes.
            Their embeddings are averaged,
            and subtracted from the input."""
            bad_vec = _aggregate_vectors(bad_movies)
            bad_vec = bad_vec / harshness
            return good_movies_vec - bad_vec

        def _score_model(recs, val_list):
            ids = [x[0] for x in recs]
            return len(list(set(ids) & set(val_list)))

        aggregated = _aggregate_vectors(input)
        recs = _similar_movies(aggregated, bad_movies, n=n)
        recs = _remove_dupes(recs, input, bad_movies)
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
