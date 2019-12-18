import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import time
import datetime
import logging
import os
import sys
import psycopg2
import spacy
from getpass import getpass
from datetime import datetime
from random import randint
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.pipeline import Pipeline
from sklearn.neighbors import NearestNeighbors
from spacy.tokenizer import Tokenizer
from spacy.lang.en import English

# Create a blank Tokenizer with just the English vocab
nlp = English()
tokenizer = Tokenizer(nlp.vocab)

# open shuffled movie id list
movie_id_df = pd.read_csv('../web_scraping/movieid_shuffle.csv',
                            encoding='ascii',
                            names=['index', 'movie_id'])

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
    tokenlist = [token.text.lower() for token in tokenizer(text)]
    return ' '.join(tokenlist)

def aggregate_reviews(review_list):
    """Combine all reviews into one string"""
    tokens = ""
    for i in review_list:
        tokens += i
        # print(i)
    return tokens

def aggregate_movies(n):
    """Combine all reviews for random n movies into a dataframe."""
    rows_list = []
    for id in movie_id_df.movie_id[:n]:
        text_list = get_review_text(id.strip('tt'))
        if len(text_list) > 0:
            # print(text_list)
            review_list = [tokenize(i[1]) for i in text_list]
            # print("\n", review_list)
            tokens = aggregate_reviews(review_list)
            # print("\n", tokens)
            movie_dict = {'movie_id':id.strip('tt'), 'tokens':tokens}
            rows_list.append(movie_dict)

    # df = pd.DataFrame(columns=['movie_id', 'tokens'])
    df = pd.DataFrame(rows_list, columns=['movie_id', 'tokens'])
    print("rows size: ", sys.getsizeof(rows_list))
    print("dataframe size: ", sys.getsizeof(df))
    print(df.shape)
    return df


# aggregate reviews from first n random movies
df = aggregate_movies(500)
nlp = spacy.load("en_core_web_sm")

# Instantiate pipeline
STOPWORDS = nlp.Defaults.stop_words
tfidf = TfidfVectorizer(stop_words=STOPWORDS)
svd = TruncatedSVD(n_components=1000) # This may be too many components.
DTMpipe = Pipeline([('tfidf', tfidf), ('svd', svd)])

# build DTM with movie_id index
dtm = DTMpipe.fit_transform(df['tokens'])
dtm = pd.DataFrame(dtm)
dtm = dtm.set_index(df['movie_id'])

# save DTM
dtm.to_csv('ReducedDTM'+str(datetime.datetime.now())+'.csv')

# instantiate and fit KNN
knn = NearestNeighbors(n_neighbors=5, algorithm='kd_tree')
knn.fit(dtm)

# test a review
test_review = ["This film is the most poignant exploration of the human condition\
                I have ever seen. The ennui, pain, dread, pathos, and love\
                on display here is overwhelming."]
review_vect = DTMpipe.transform(test_review)
for i in knn.kneighbors(review_vect)[1][0]:
    print(dtm.index[i])

# give receommendations for user input
user_review = [input("Paste a movie review here:  ")]
user_review_vect = DTMpipe.transform(user_review)
for i in knn.kneighbors(user_review_vect)[1][0]:
    print("https://www.imdb.com/title/tt" + str(dtm.index[i]))

# close connection
if connection:
  cursor_boi.close()
  connection.close()
