import psycopg2
import pandas as pd
import os
from decouple import config
from tqdm import tqdm



def seventoten(username):
    '''
    accepting a username, this function returns user ratings greater than seven
    and movie_ids of the user 
    '''
    name = username
    sql = f'''SELECT user_rating, movie_id FROM reviews WHERE username = '{name}' 
              AND user_rating BETWEEN 7 AND 10'''

    connection = psycopg2.connect(
    database  = "postgres",
    user      = "postgres",
    password  = os.getenv('DB_PASSWORD'),
    host      = "movie-rec-scrape.cvslmiksgnix.us-east-1.rds.amazonaws.com",
    port      = '5432')
    dat = pd.read_sql_query(sql, connection)
    connection = None
    return dat

def query2(username):
    '''
    accepting a username, this function will return all their reviewed movies as a nested list
    '''
    name = username
    sql = f"SELECT movie_id FROM reviews WHERE username = '{name}'"

    connection = psycopg2.connect(
    database  = "postgres",
    user      = "postgres",
    password  = os.getenv('DB_PASSWORD'),
    host      = "movie-rec-scrape.cvslmiksgnix.us-east-1.rds.amazonaws.com",
    port      = '5432')
    cursor = connection.cursor()
    cursor.execute(sql)
    result = cursor.fetchall()
    rows=[[i[0]] for i in result]
    connection = None
    return rows

def id_to_title(list):
    '''
    accepting a list of movie ids outputted from the model, this function 
    will change those ids to titles
    '''
    sql = f"SELECT title FROM movies WHERE movie_id IN '{list}'"
    connection = psycopg2.connect(
    database  = "postgres",
    user      = "postgres",
    password  = os.getenv('DB_PASSWORD'),
    host      = "movie-rec-scrape.cvslmiksgnix.us-east-1.rds.amazonaws.com",
    port      = '5432')
    cursor = connection.cursor()
    cursor.execute(sql)
    result = list(cursor.fetchall())
    connection = None
    return result

def connect_to_DB():
    connection = psycopg2.connect(
    database  = "postgres",
    user      = "postgres",
    password  = config('PASSWORD'),
    host      = "movie-rec-scrape.cvslmiksgnix.us-east-1.rds.amazonaws.com",
    port      = '5432')
    cursor = connection.cursor()
    return cursor


def get_imdb_users():
    '''
    returns a list of all of the unique usernames in the IMDB username column
    '''
    cursor = connect_to_DB()
    query = f"SELECT username From reviews"
    cursor.execute(query)
    result = list(cursor.fetchall())
    cursor.close()
    users = []
    for name in tqdm(result):
        users.append(name[0])

    unique_users = set(users)
    unique_users = list(unique_users)
    unique_users.sort()
    return unique_users

def imdb_user_lookup(username):
    '''
    takes in a username and searches the data base for all of the reviews made by that user and 
    returns a dataframe.
    '''
    users = get_imdb_users()
    return users

