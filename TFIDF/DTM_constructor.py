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
import pandas as pd
from random import randint

# open shuffled movie id list
df = pd.read_csv('movieid_shuffle.csv', encoding='ascii')

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
    """Get all reviews for a movie_id. Returns ... ?"""
    movie_query = "SELECT review_text FROM reviews WHERE movie_id=" \
                + str(id)

    # execute query
    results = cursor_boi.execute(query)
    connection.commit()
    print(results)

get_review_text(32143)

# close connection
if connection:
  cursor_boi.close()
  connection.close()
