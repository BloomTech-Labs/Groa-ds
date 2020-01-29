import datetime
import logging
import multiprocessing
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
import time
from bs4 import BeautifulSoup
from datetime import datetime
from gensim.models.doc2vec import Doc2Vec, TaggedDocument
from gensim.parsing.preprocessing import STOPWORDS
from gensim.utils import tokenize as gtokenize
from gensim.utils import lemmatize, simple_preprocess
from getpass import getpass
from random import randint
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors
from sklearn.pipeline import Pipeline

"""
This script opens a setup wizard for a movie recommender model based on the
similarity of users' review styles.

Before any inferencing can take place, all of a user's movie reviews are tokenized and
joined together into one list. The resulting list of tokens is used to train Doc2Vec.

The process is broken into steps because the first-time setup can take a long time.
If there is a network error, all prepared training data will persist in 5000-user
files.

The fully trained model can transform a similarly tokenized review history into
a 100-dimensional vector, which is used to find similar reviewers. Ultimately,
this model will function as a complement to the more traditional user-based
collaborative-filtering model, "w2v_limitingfactor_v1". This "Review2Vec" model
is thought to have the advantage of finding less obvious recommendations using
the most salient parts of a user's reviews.
"""

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

# set number of cores for faster training
n_cpus = multiprocessing.cpu_count()

# make rows folder if it doesn't exist yet
os.makedirs('rows/', exist_ok=True)

my_time = time.time()
def timer_func(x=None):
    """Prints seconds passed since last checkpoint, for debugging purposes."""
    global my_time
    if x is not None:
        print(x, time.time() - my_time)
    my_time = time.time()

def get_user_list():
    """Get a list of users"""
    user_query = """SELECT username
	                FROM reviews
	                GROUP BY username
	                HAVING COUNT(username) >= 6"""
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
    The files in this directory are serialized lists of aggregated movie reviews.
    Returns the position of the user list to pick back up at."""
    # If rows folder is empty, then return 0 (start at the beginning).
    # If rows folder is not empty, return the largest number in a filename.
    p = pathlib.Path("./rows")
    files = [path.parts[1] for path in p.iterdir() if path.is_file()]
    if len(files) == 0:
        print("dir 'rows' is empty")
        return 0
    elif len(files) != 0:
        # highest numbered file in directory
        return max([int(re.sub(r'[^0-9]', '', x)) for x in files])
    else:
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
    """Attempt to get all users downloaded and serialized. Pickup where
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
    """Combine all review histories for n users into a list."""
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

def setup():
    """Setup wizard."""
    global user_list
    while True:
        print("""Options: \n
                    (0) Update the list of users. \n
                    (1) Serialize all reviews on a per user basis, or up to a certain point. \n
                    (2) Check how many users have been serialized. \n
                    (3) Not in use. \n
                    (4) Train Review2Vec. Pickle the model. \n
                    (5) Train Review2Vec over several hyperparams. Pickle models. \n
                    (6) Get movie recommendations given test input. \n
                    (7) Exit this setup wizard with the DB connection open.
                     """)
        try:
            choice = int(input("Enter a choice: "))
        except ValueError:
            continue
        if choice == 0:
            print("Updating user list from database...")
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
            # # Instantiate pipeline
            # tfidf = TfidfVectorizer(stop_words=STOPWORDS)
            # svd = TruncatedSVD(n_components=1000) # This may be too many components.
            # PickleMePipe = Pipeline([('tfidf', tfidf), ('svd', svd)])
            #
            # # create a DataFrame
            # small_df = create_df(5000)
            #
            # # fit the pipeline and pickle it
            # small_dtm = PickleMePipe.fit_transform(small_df['tokens'])
            # pickling_on = open("Pipeline.pickle", "wb")
            # pickle.dump(PickleMePipe, pickling_on)
            # pickling_on.close()
            # print("Pipeline has been pickled.")
            #
            # # save DTM
            # small_dtm.to_csv('small_dtm.csv')
            # print("Small DTM has been pickled.")
            continue
        if choice == 4:
            # train word2vec model
            print("getting pickled list")
            documents = get_pickled_list(check_row_files())
            train_list = [TaggedDocument(doc['tokens'], doc['username'])
                            for doc in documents]

            model = Doc2Vec(documents = train_list,
                            vector_size = 100,
                            # window = 10, # perhaps increase this
                            workers = n_cpus, # use all cores
                            hs = 0, # must be set to 0 for negative sampling
                            negative = 10, # for negative sampling
                            ns_exponent = 0.75,
                            alpha=0.03, min_alpha=0.0007,
                            seed = 14
                            )
            print("training Review2Vec...")
            model.train(train_list, total_examples = model.corpus_count,
                        epochs=20, # best results set this 90-150
                        report_delay=60)
            print("\n\n//////MODEL TRAINED\\\\\\ \n\n")
            # save word2vec model
            model.save("r2v_Botanist_v1.model")
            continue

        if choice == 5:
            # train word2vec model
            print("getting pickled list")
            documents = get_pickled_list(check_row_files())
            train_list = [TaggedDocument(doc['tokens'], doc['username'])
                            for doc in documents]
            params = {
                        (100,0.75),
                        (100,0.5),
                        (200,0.75),
                        (200,0.5),
                    }
            for vector_size, ns_exponent in params:
                model = Doc2Vec(documents = train_list,
                                vector_size = vector_size,
                                # window = window, # perhaps increase this
                                workers = n_cpus, # use all cores
                                hs = 0, # must be set to 0 for negative sampling
                                negative = 10, # for negative sampling
                                ns_exponent = ns_exponent,
                                alpha=0.03, min_alpha=0.0007,
                                seed = 14
                                )
                print("training Review2Vec...")
                model.train(train_list, total_examples = model.corpus_count,
                            epochs=50, # best results set this 90-150
                            report_delay=60)
                print(f"\n\n//////MODEL TRAINED\\\\\\ \n\n")
                # save word2vec model
                model.save(f"""r2v_Botanist_v1.{str(vector_size)}{str(ns_exponent)[1:]}.model""")

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
            results = [x[0] for x in results]
            print("most similar users: \n", results)

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
