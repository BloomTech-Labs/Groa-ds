import psycopg2
import pandas as pd
from decouple import config


def query(username):
    '''
    accepting a username, this function returns user ratings and reviews of the user
    '''
    name = username
    sql = f"SELECT user_rating, review_text FROM reviews WHERE username = '{name}'"

    connection = psycopg2.connect(
    database  = "postgres",
    user      = "postgres",
    password  = config('DB_PASSWORD'),
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
    password  = config('DB_PASSWORD'),
    host      = "movie-rec-scrape.cvslmiksgnix.us-east-1.rds.amazonaws.com",
    port      = '5432')
    cursor = connection.cursor()
    cursor.execute(sql)
    result = cursor.fetchall()
    rows=[[i[0]] for i in result]
    connection = None
    return rows

def query3(list):
    '''
    accepting a list of movie ids outputted from the model, this function 
    will change those ids to titles
    '''
    sql = f"SELECT title FROM movies WHERE movie_id IN '{list}'"
    connection = psycopg2.connect(
    database  = "postgres",
    user      = "postgres",
    password  = config('DB_PASSWORD'),
    host      = "movie-rec-scrape.cvslmiksgnix.us-east-1.rds.amazonaws.com",
    port      = '5432')
    cursor = connection.cursor()
    cursor.execute(sql)
    result = list(cursor.fetchall())
    connection = None
    return result