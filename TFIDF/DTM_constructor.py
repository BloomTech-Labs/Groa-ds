import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import time
import logging
import os
import psycopg2
import spacy
from getpass import getpass
from datetime import datetime
from random import randint

# open shuffled movie id list
# df = pd.read_csv('movieid_shuffle.csv', encoding='ascii')

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
    """Returns a list of tokens from text"""
    tokens = re.sub(r'[^a-zA-Z ^0-9]','', text)
    tokens = tokens.lower().split()
    return tokens

get_review_text(32143)



# close connection
if connection:
  cursor_boi.close()
  connection.close()
