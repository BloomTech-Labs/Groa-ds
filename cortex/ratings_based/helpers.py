import pandas as pd
import re 

id_book = pd.read_csv('exported_data/title_basics_small.csv')

def fill_id(id):
    """Adds leading zeroes back if necessary. This makes the id match the database."""
    if len(str(id)) < 7:
        length = len(str(id))
        id = "0"*(7 - length) + str(id)
    return str(id)
    
def df_to_id_list(df, id_book):
    """Converts dataframe of movies to a list of the IDs for those movies.

    Every title in the input dataframe is checked against the local file, which
    includes all the titles and IDs in our database. For anything without a match,
    replace the non-alphanumeric characters with wildcards, and query the database
    for matches.
    """
    df['Year'] = df['Year'].astype(int).astype(str)
    """ riley edit """
    matched = pd.merge(df, id_book,
                left_on=['Name', 'Year'], right_on=['primaryTitle', 'startYear'],
                how='inner')
#     matched = pd.merge(df, id_book,
#                 left_on=['Title', 'Year'], right_on=['primaryTitle', 'startYear'],
#                 how='inner')
    ids = matched['tconst'].astype(str).tolist()
    final_ratings = []
    """ riley edit """
    names = df.Name.tolist()
#     names = df.Title.tolist()
    years = [int(year) for year in df.Year.tolist()]
    if 'Rating' in df.columns:
        stars = [int(rating) for rating in df.Rating.tolist()]
        info = list(zip(names, years, stars))
        final_ratings = matched['Rating'].astype(int).tolist()
    else:
        info = list(zip(names, years, list(range(len(years)))))
    missed = [x for x in info if x[0] not in matched['primaryTitle'].tolist()]
    for i, j, k in missed:
        i = re.sub('[^\s0-9a-zA-Z\s]+', '%', i)
        try:
            cursor_dog.execute(f"""
                SELECT movie_id, original_title, primary_title
                FROM imdb_movies
                WHERE primary_title ILIKE '{i}' AND start_year = {j}
                  OR original_title ILIKE '{i}' AND start_year = {j}
                ORDER BY runtime_minutes DESC
                LIMIT 1""")
            id = cursor_dog.fetchone()[0]
            ids.append(id)
            final_ratings.append(k)
        except:
            continue
    ids = [fill_id(id) for id in ids]
    final_ratings = [x*2 for x in final_ratings]
    ratings_dict = dict(zip(ids, final_ratings))
    return tuple([ids, ratings_dict])
    
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
        good_list, good_dict = df_to_id_list(good_df, id_book)
        bad_list, bad_dict = df_to_id_list(bad_df, id_book)
        neutral_list, neutral_dict = df_to_id_list(neutral_df, id_book)
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
        """ add rileys code """
#         good_list, good_dict = df_to_id_list(good_df, id_book)
#         bad_list, bad_dict = df_to_id_list(bad_df, id_book)
#         neutral_list, neutral_dict = df_to_id_list(neutral_df, id_book)
        
    except Exception as e:
        # can't read the dataframe as Letterboxd or IMDb user data
        print("This dataframe has columns:", ratings_df.columns)
        raise Exception(e)
        
    ratings_dict = dict(list(good_dict.items()) + list(bad_dict.items()) + list(neutral_dict.items()))

    if watched_df is not None:
        # Construct list of watched movies that aren't rated "good" or "bad"
        # First, get a set of identified IDs.
        rated_names = set(good_df.Name.tolist() + bad_df.Name.tolist() + neutral_list)
        # drop nulls from watched dataframe
        full_history = watched_df.dropna(axis=0, subset=['Name', 'Year'])
        # get list of watched movies that haven't been rated
        hist_list = df_to_id_list(full_history[~full_history['Name'].isin(rated_names)], id_book)[0]
        # add back list of "neutral" movies (whose IDs we already found before)
        hist_list = hist_list + neutral_list
    else: hist_list = neutral_list

    if watchlist_df is not None:
        try:
            watchlist_df = watchlist_df.dropna(axis=0, subset=['Name', 'Year'])
            val_list = df_to_id_list(watchlist_df, id_book)[0]
        except KeyError:
            watchlist_df = watchlist_df.dropna(axis=0, subset=['Const', 'Year'])
            watchlist_df['movie_id'] = watchlist_df['Const'].str.lstrip("tt")
            val_list = watchlist_df['movie_id'].tolist()
    else: val_list = []

    return (good_list, bad_list, hist_list, val_list, ratings_dict)