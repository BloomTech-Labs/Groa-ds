import gensim
import numpy as np
import pandas as pd
import psycopg2
import re
from decouple import config

def connect_db():
    """connect to database, create cursor"""
    # connect to database
    connection = psycopg2.connect(
        database  = "postgres",
        user      = "postgres",
        password  = config('DB_PASSWORD'),
        host      = "groalives.cvslmiksgnix.us-east-1.rds.amazonaws.com",
        port      = '5432'
    )
    # create cursor that is used throughout
    try:
        c = connection.cursor()
        print("Connected!")
    except:
        print("Connection problem chief!")
    # Enter database password and press Enter.

def fill_id(id):
    """Adds leading zeroes back if necessary. This makes the id match the database."""
    if len(str(id)) < 7:
        length = len(str(id))
        id = "0"*(7 - length) + str(id)
    return str(id)

def df_to_id_list(df):
    """Converts dataframe of movies to a list of the IDs for those movies.

    Every title in the input dataframe is checked against the local file, which
    includes all the titles and IDs in our database. For anything without a match,
    replace the non-alphanumeric characters with wildcards, and query the database
    for matches.
    """
    df['Year'] = df['Year'].astype(int).astype(str)
    names = df.Name.tolist()
    years = [int(year) for year in df.Year.tolist()]
    info = list(zip(names, years))
    matched = pd.merge(df, id_book,
               left_on=['Name', 'Year'], right_on=['primaryTitle', 'startYear'],
               how='inner')
    ids = matched['tconst'].astype(str).tolist()
    missed = [x for x in info if x[0] not in matched['primaryTitle'].tolist()]
    for i, j in missed:
        i = re.sub('[^\s0-9a-zA-Z\s]+', '%', i)
        try:
            c.execute(f"""
                SELECT movie_id, original_title, primary_title
                FROM movies
                WHERE primary_title ILIKE '{i}' AND start_year = {j}
                  OR original_title ILIKE '{i}' AND start_year = {j}
                ORDER BY runtime_minutes DESC
                LIMIT 1""")
            id = c.fetchone()[0]
            ids.append(id)
        except:
            continue
    return [fill_id(id) for id in ids]

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
        # try to read Letterboxd user data
        # drop rows with nulls in the columns we use
        ratings_df = ratings_df.dropna(axis=0, subset=['Rating', 'Name', 'Year'])
        # split according to user rating
        good_df = ratings_df[ratings_df['Rating'] >= good_threshold]
        bad_df = ratings_df[ratings_df['Rating'] <= bad_threshold]
        neutral_df = ratings_df[(ratings_df['Rating'] > bad_threshold) & (ratings_df['Rating'] < good_threshold)]
        # convert dataframes to lists
        good_list = df_to_id_list(good_df)
        bad_list = df_to_id_list(bad_df)
        neutral_list = df_to_id_list(neutral_df)
    except KeyError:
        # Try to read IMDb user data
        # strip ids of "tt" prefix
        ratings_df['movie_id'] = ratings_df['Const'].str.lstrip("tt")
        # drop rows with nulls in the columns we use
        ratings_df = ratings_df.dropna(axis=0, subset=['Your Rating', 'Year'])
        # split according to user rating
        good_df = ratings_df[ratings_df['Your Rating'] >= good_threshold*2]
        bad_df = ratings_df[ratings_df['Your Rating'] <= bad_threshold*2]
        neutral_df = ratings_df[(ratings_df['Your Rating'] > bad_threshold*2) & (ratings_df['Your Rating'] < good_threshold*2)]
        # convert dataframes to lists
        good_list = good_df['movie_id'].to_list()
        bad_list = bad_df['movie_id'].to_list()
        neutral_list = neutral_df['movie_id'].to_list()
    except Exception as e:
        # can't read the dataframe as Letterboxd or IMDb user data
        print("This dataframe has columns:", ratings_df.columns)
        raise Exception(e)

    if watched_df is not None:
        # Construct list of watched movies that aren't rated "good" or "bad"
        # First, get a set of identified IDs.
        rated_names = set(good_df.Name.tolist() + bad_df.Name.tolist() + neutral_list)
        # drop nulls from watched dataframe
        full_history = watched_df.dropna(axis=0, subset=['Name', 'Year'])
        # get list of watched movies that haven't been rated
        hist_list = df_to_id_list(full_history[~full_history['Name'].isin(rated_names)])
        # add back list of "neutral" movies (whose IDs we already found before)
        hist_list = hist_list + neutral_list
    else: hist_list = neutral_list

    if watchlist_df is not None:
        try:
            watchlist_df = watchlist_df.dropna(axis=0, subset=['Name', 'Year'])
            val_list = df_to_id_list(watchlist_df)
        except KeyError:
            watchlist_df = watchlist_df.dropna(axis=0, subset=['Const', 'Year'])
            watchlist_df['movie_id'] = watchlist_df['Const'].str.lstrip("tt")
            val_list = watchlist_df['movie_id'].tolist()
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
            all_rated = input + bad_movies
            if hist_list:
                all_rated = list(set(all_rated+hist_list))
            nonlocal dupes
            dupes = [x for x in recs if x[0] in all_rated]
            return [x for x in recs if x[0] not in all_rated]

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
