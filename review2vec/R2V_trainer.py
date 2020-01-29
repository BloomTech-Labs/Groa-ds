import datetime
import logging
import time
import nltk
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
from gensim.models.doc2vec import Doc2Vec, TaggedDocument
from gensim.utils import tokenize as gtokenize
from gensim.utils import lemmatize, simple_preprocess
from gensim.parsing.preprocessing import STOPWORDS
from getpass import getpass
from random import randint
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.neighbors import NearestNeighbors

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

# open shuffled movie id list
# rand_index is the index. Renamed to avoid namespace issues.
movie_id_df = pd.read_csv('movieid_shuffle.csv',
                            encoding='ascii',
                            names=['rand_index', 'movie_id'])

# initialize stopwords
STOPWORDS = list(STOPWORDS)


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

# list of users
user_list = None

def get_user_list():
    """Get a list of users"""
    user_query = """SELECT DISTINCT username from reviews"""
    cursor_boi.execute(user_query)
    user_list = cursor_boi.fetchall()
    print(len(user_list), "users found!")
    return user_list

def get_review_text(username):
    """Get all reviews for a user. Returns list of tuples from DB."""
    movie_query = f"""SELECT review_text
                      FROM reviews
                      WHERE username='{str(username[0])}'
                      ORDER BY review_date ASC"""

    # execute query
    cursor_boi.execute(movie_query)
    result = cursor_boi.fetchall()
    return result

def tokenize(text):
    """Returns a list of tokens from text"""
    tokens = simple_preprocess(text)
    tokens = [token for token in tokens if token not in STOPWORDS]
    return tokens

def aggregate_reviews(review_list):
    """Combine all review tokens into one string."""
    reviews = ""
    for i in review_list:
        reviews += i[0]
    return reviews.lower()

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
    for id in user_list[pickup:end]:
        text_list = get_review_text(id)
        if len(text_list) > 0:
            reviews = aggregate_reviews(text_list)
            tokens = tokenize(reviews)
            user_dict = {'username':id, 'tokens':tokens}
            rows_list.append(user_dict)
    # pickle list of rows, with the ending row as file name.
    pickling_on = open(f"rows/{end}.pickle","wb")
    pickle.dump(rows_list, pickling_on)
    pickling_on.close()
    return None

def batch_get_all_movies():
    """Attempt to get all movies downloaded and serialized. Pickup where
    the last attempt left off."""
    goal = len(user_list)
    pickup = check_row_files()
    for i in range(5000, goal, 5000):
        print(f"Batch serializing the next 5000 users (to {i}).")
        batch_serialize(pickup, i)
    if goal % 5000 != 0:
        remainder = goal % 5000
        batch_serialize(goal - remainder, goal)
    return True

def get_pickled_list(n: int):
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
    print("rows size: ", sys.getsizeof(rows_list))
    return rows_list

def train_w2v():
    pass

def create_df():
    """dummy for deprecated references"""
    pass

def setup():
    """Setup wizard."""
    global user_list
    while True:
        print("""Options: \n
                    (0) Get a list of users. \n
                    (1) Serialize all reviews on a per user basis, or up to a certain point. \n
                    (2) Check how many users have been serialized. \n
                    (3) Fit a tokenizer on all the reviews. pickle it \n
                    (4) Tokenize all reviews and serialize them as lists. \n
                    (5) Train Word2Vec on review lists. Pickle the model. \n
                    (6) Get movie recommendations given test input. \n
                    (7) Exit this setup wizard with the DB connection open.
                     """)
        try:
            choice = int(input("Enter a choice: "))
        except ValueError:
            continue
        if choice == 0:
            try:
                unpickling_users = open('users.pickle', 'rb')
                print("unpickling users doc...")
                user_list = pickle.load(unpickling_users)
            except:
                print("no users doc found; getting from database...")
                user_list = get_user_list()
                pickling_users = open('users.pickle', 'wb')
                print("pickling it...")
                pickle.dump(user_list, pickling_users)
        if choice == 1:
            if user_list is None:
                user_list = get_user_list()
            pickup = check_row_files()
            print(f"""Users serialized: {pickup}""")
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
            print(f"Users serialized: {pickup}")
        if choice == 2:
            pickup = check_row_files()
            print(f"Users serialized: {pickup}")
        if choice == 3:
            # Instantiate pipeline
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
            # train word2vec model
            print("getting pickled list")
            documents = get_pickled_list(check_row_files())
            print(documents[0])
            # test_user = documents[0][1]
            train_list = [TaggedDocument(doc['tokens'], doc['username']) for doc in documents]
            print(train_list[0])
            model = Doc2Vec(documents = train_list,
                            vector_size = 100,
                            # window = 10, # perhaps increase this
                            hs = 0, # must be set to 0 for negative sampling
                            negative = 10, # for negative sampling
                            ns_exponent = 0.75,
                            alpha=0.03, min_alpha=0.0007,
                            seed = 14
                            )
            # print("building vocab...")
            # model.build_vocab(train_list, progress_per=200)
            print("training Review2Vec...")
            model.train(train_list, total_examples = model.corpus_count,
                        epochs=20, # best results set this 90-150
                        report_delay=60)
            print("\n\n//////MODEL TRAINED\\\\\\ \n\n")
            # save word2vec model
            model.save("r2v_Botanist_v1.model")

        if choice == 6:
            # load the model
            model = Doc2Vec.load('r2v_Botanist_v1.model')
            # load test reviews
            pickling_off = open('coop_reviews.pickle', 'rb')
            # tokenize reviews
            test_review = pickle.load(pickling_off)
            test_review = [tuple([x, '']) for x in test_review]
            test_aggregated_tokens = aggregate_reviews(test_review)
            test_tokens = tokenize(test_aggregated_tokens)
            test_vec = model.infer_vector(test_tokens)
            results = model.docvecs.most_similar([test_vec], topn= 10)
            print(results)
            
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
