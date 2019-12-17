import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import time
import logging
import os
import psycopg2
from getpass import getpass
from datetime import datetime
from random import randint
from sklearn.feature_extraction.text import TfidfVectorizer


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
            movie_dict = {'movie_id':id, 'tokens':tokens}
            rows_list.append(movie_dict)

    # df = pd.DataFrame(columns=['movie_id', 'tokens'])
    df = pd.DataFrame(rows_list, columns=['movie_id', 'tokens'])
    print(df.shape)
    return df


# close connection
if connection:
  cursor_boi.close()
  connection.close()
