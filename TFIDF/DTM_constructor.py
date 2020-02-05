import datetime
import logging
import time
import os
import pandas as pd
import pathlib
import pickle
import psycopg2
import re
import requests
import spacy
import sys
from bs4 import BeautifulSoup
from datetime import datetime
from getpass import getpass
from random import randint
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.neighbors import NearestNeighbors
from spacy.tokenizer import Tokenizer
from spacy.lang.en import English

"""
This script opens a setup wizard for a movie recommender model (after the user
enters the password to the database where movie reviews are held). The process
is broken into steps because the first-time setup can take a long time. Before
any inferencing can take place, all movie reviews are joined together into one
string per movie, and the resulting string is used to create a Document-Term-Matrix.

Since the matrix in question needs to have a small number of terms for fast inferencing,
Truncated SVD is used directly following TF-IDF vectorizer. The pipeline of these
two algorithms is fitted on a small matrix and then used to create the master.

Once the master (reduced) DTM is created, it can be used with KNN to find movies
with similar reviews to the input review.

NOTE: in this version, the only acceptable input reviews are plain text with no
" or ' symbols.
"""

# Create a blank Tokenizer with just the English vocab
# nlp = English()
# This english corpus has to be installed locally, so it's good to check for first.
try:
    nlp = spacy.load("en_core_web_sm")
except:
    os.system("python -m spacy download en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")
tokenizer = Tokenizer(nlp.vocab)

# open shuffled movie id list
# rand_index is the index. Renamed to avoid namespace issues.
movie_id_df = pd.read_csv('../web_scraping/movieid_shuffle.csv',
                            encoding='ascii',
                            names=['rand_index', 'movie_id'])

# connect to database
connection = psycopg2.connect(
    database  = "postgres",
    user      = "postgres",
    password  = getpass(),
    host      = "movie-rec-scrape.cvslmiksgnix.us-east-1.rds.amazonaws.com",
    port      = '5432'
)

# cursor object
try:
    cursor_boi = connection.cursor()
    print("Connected!")
except:
    print("Connection problem chief!")

# Control for optional connection closing
close_me = True

def get_review_text(id):
    """Get all reviews for a movie_id. Returns list of tuples from DB."""
    movie_query = "SELECT movie_id, review_text FROM reviews WHERE movie_id=" \
                + str(id)

    # execute query
    cursor_boi.execute(movie_query)
    result = cursor_boi.fetchall()
    return result

def tokenize(text):
    """Returns a string of tokens from text"""
    tokens = re.sub(r'[^a-zA-Z ^0-9]','', text)
    tokens = tokens.lower()
    return tokens

def spacy_tokenize(text):
    """Tokenize with spacy. Currently not in use."""
    tokenlist = [token.text.lower() for token in tokenizer(text)]
    return ' '.join(tokenlist)

def aggregate_reviews(review_list):
    """Combine all reviews into one string."""
    tokens = ""
    for i in review_list:
        tokens += i
        # print(i)
    return tokens

def check_row_files():
    """Check for the existence of rows in the rows directory.
    The files in this directory are serialized lists of aggrgated movie reviews.
    They're stored in this format so that they can be used to construct the
    master DTM all at once, which is necessary because appending to a DataFrame
    involves copying the entire thing. This method should make the process happen
    much faster.

    Returns the position of the movieid_shuffle.csv to pick back up at."""
    # If rows folder is empty, then return 0 (start at the beginning).
    # If rows folder is not empty, return the largest number in a filename.
    p = pathlib.Path("./rows")
    files = [path.parts[1] for path in p.iterdir() if path.is_file()]
    if len(files) == 0:
        print("dir 'rows' is empty")
        return 0
    elif len(files) != 0:
        return max([int(re.sub(r'[^0-9]', '', x)) for x in files])
    else:
        print("dir 'rows' does not seem empty or non-empty. Weird!")
        return 0

def batch_serialize(start: int, end: int):
    """Serialize a list of aggregated reviews starting and ending with a
    certain point in the movieid_shuffle.csv."""
    pickup = check_row_files()
    if pickup > end:
        return None
    rows_list = []
    for id in movie_id_df.movie_id[pickup:end]:
        text_list = get_review_text(id.strip('tt'))
        if len(text_list) > 0:
            # print(text_list)
            review_list = [tokenize(i[1]) for i in text_list]
            # print("\n", review_list)
            tokens = aggregate_reviews(review_list)
            # print("\n", tokens)
            movie_dict = {'movie_id':id.strip('tt'), 'tokens':tokens}
            rows_list.append(movie_dict)
    # pickle list of rows, with the ending row as file name.
    pickling_on = open(f"rows/{end}.pickle","wb")
    pickle.dump(rows_list, pickling_on)
    pickling_on.close()
    return None

def batch_get_all_movies():
    """Attempt to get all movies downloaded and serialized. Pickup where
    the last attempt left off."""
    goal = len(movie_id_df.movie_id)
    pickup = check_row_files()
    for i in range(5000, goal, 5000):
        print(f"Batch serializing the next 5000 movies (to {i}).")
        batch_serialize(pickup, i)
    if goal % 5000 != 0:
        remainder = goal % 5000
        batch_serialize(goal - remainder, goal)
    return True

def create_df(n: int):
    """Combine all reviews for a certain number of movie reviews into a dataframe."""
    # Get any rows that aren't already serialized.
    pickup = check_row_files()
    if pickup < n:
        batch_serialize(pickup, n)
    # unpickle the rows specified by n.
    rows_list = []
    p = pathlib.Path("./rows")
    files = [path for path in p.iterdir() if path.is_file()]
    file_numbers = [int(re.sub(r'[^0-9]', '', path.parts[1])) for path in p.iterdir() if path.is_file()]
    for number in file_numbers:
        if number <= n:
            pickling_off = open(f"./rows/{number}.pickle", "rb")
            temp_list = pickle.load(pickling_off)
            rows_list.extend(temp_list)
    # Construct DataFrame
    df = pd.DataFrame(rows_list, columns=['movie_id', 'tokens'])
    print("rows size: ", sys.getsizeof(rows_list))
    print("dataframe size: ", sys.getsizeof(df))
    print(df.shape)
    return df

def setup():
    """Setup wizard."""
    while True:
        print("""Options: \n
                    (1) Serialize all reviews, or up to a certain point. \n
                    (2) Check how many reviews have been serialized. \n
                    (3) Fit a pipeline on a small dataframe, and pickle both. \n
                    (4) Create a dataframe from all the reviews. \n
                    (5) Transform the dataframe with the pipeline. \n
                    (6) Get movie recommendations. \n
                    (7) Exit this setup wizard with the DB connection open.
                     """)
        choice = int(input("Enter a choice: "))
        if choice == 1:
            pickup = check_row_files()
            print(f"""Movies serialized: {pickup}""")
            print("""Options: \n
                    (1) Serialize all reviews. \n
                    (2) Or enter a number greater than 1 to specify how many.""")
            second_choice = int(input("Enter a choice: "))
            if second_choice == 1:
                batch_get_all_movies()
            if second_choice > 1:
                print(f"serializing movies from {pickup} to {second_choice}")
                batch_serialize(pickup, second_choice)
            pickup = check_row_files()
            print(f"Movies serialized: {pickup}")
        if choice == 2:
            pickup = check_row_files()
            print(f"Movies serialized: {pickup}")
        if choice == 3:
            # Instantiate pipeline
            STOPWORDS = nlp.Defaults.stop_words
            tfidf = TfidfVectorizer(stop_words=STOPWORDS)
            svd = TruncatedSVD(n_components=1000) # This may be too many components.
            PickleMePipe = Pipeline([('tfidf', tfidf), ('svd', svd)])

            # create a DataFrame
            small_df = create_df(5000)

            # fit the pipeline and pickle it
            small_dtm = PickleMePipe.fit_transform(small_df['tokens'])
            pickling_on = open("Pipeline.pickle", "wb")
            pickle.dump(PickleMePipe, pickling_on)
            pickling_on.close()
            print("Pipeline has been pickled.")

            # save DTM
            small_dtm.to_csv('small_dtm.csv')
            print("Small DTM has been pickled.")

        if choice == 4:
            # Make master DataFrame from whatever rows are currently serialized.
            all_movies = check_row_files()
            master_df = create_df(all_movies)
            print("""\n\n//////MASTER DATAFRAME CREATED\\\\\\\ \n\n""")
            print(f"""shape:{master_df.shape}""")
        if choice == 5:
            # Load the Pipeline
            pickling_off = open(f"Pipeline.pickle", "rb")
            FrankenPipe = pickle.load(pickling_off)
            # Construct master document-term matrix.
            master_dtm = FrankenPipe.transform(master_df['tokens'])
            master_dtm = pd.DataFrame(master_dtm)
            master_dtm = master_dtm.set_index(master_df['movie_id'])
            print("\n\n//////MASTER DOCUMENT-TERM MATRIX CREATED\\\\\\\ \n\n""")
        if choice == 6:
            # Load the Pipeline
            pickling_off = open(f"Pipeline.pickle", "rb")
            FrankenPipe = pickle.load(pickling_off)
            # instantiate and fit KNN
            knn = NearestNeighbors(n_neighbors=10, algorithm='kd_tree')
            knn.fit(master_dtm)

            # test a review
            test_review = ["This film is the most poignant exploration of the human condition\
                            I have ever seen. The ennui, pain, dread, pathos, and love\
                            on display here is overwhelming."]
            review_vect = FrankenPipe.transform(test_review)
            print("Here's an example review: ", test_review)
            for i in knn.kneighbors(review_vect)[1][0]:
                print("...And some example recommendations: \n")
                print("    https://www.imdb.com/title/tt" + str(master_dtm.index[i]))

            # give recommendations for user input
            user_review = [input("\nPaste a movie review here (no \" or \' symbols):  ")]
            user_review_vect = FrankenPipe.transform(user_review)
            for i in knn.kneighbors(user_review_vect)[1][0]:
                print("    https://www.imdb.com/title/tt" + str(master_dtm.index[i]))
        if choice == 7:
            # Turn off the connection closure setting so the database can be
            # accessed in interactive mode.
            global close_me
            close_me = False
            break


setup()

# close connection
if close_me:
  cursor_boi.close()
  connection.close()
