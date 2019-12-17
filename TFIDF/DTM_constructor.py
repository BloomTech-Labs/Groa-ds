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

# def aggregate_movies(data, dtm)
rows_list = []
movie_id_list = ['0000502',
'0000574',
'0000679',
'0001756',
'0002101',
'0002315',
'0002423',
'0002445',
'0002452',
'0002625',
'0002646',
'0002685',
'0002885',
'0002898',
'0003014',
'0003102',
'0003113',
'0003150',
'0003159',
'0003165',
'0003241',
'0003309',
'0003330',
'0003362',
'0003419',
'0003471',
'0003489',
'0003565',
'0003637',
'0003643',
'0003657',
'0003670',
'0003675',
'0003740'
]
for id in movie_id_df.movie_id[:300]:
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


# close connection
if connection:
  cursor_boi.close()
  connection.close()
