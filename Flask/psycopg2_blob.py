import psycopg2
import pandas as pd
import os
#from tqdm import tqdm

def seventoten(username):
    '''
    accepting a username, this function returns user ratings greater than seven
    and movie_ids of the user
    '''
    name = username
    sql = f'''SELECT user_rating, movie_id FROM reviews WHERE username = %s
              AND user_rating BETWEEN 7 AND 10'''

    connection = psycopg2.connect(
    database  = "postgres",
    user      = "postgres",
    password  = os.getenv('DB_PASSWORD'),
    host      = "movie-rec-scrape.cvslmiksgnix.us-east-1.rds.amazonaws.com",
    port      = '5432')
    dat = pd.read_sql_query(sql, connection, params=[username])
    connection = None
    return dat

def query2(username):
    '''
    accepting a username, this function will return all their reviewed movies as a nested list
    '''
    name = username
    sql = f"SELECT movie_id FROM reviews WHERE username = %s"

    connection = psycopg2.connect(
    database  = "postgres",
    user      = "postgres",
    password  = os.getenv('DB_PASSWORD'),
    host      = "movie-rec-scrape.cvslmiksgnix.us-east-1.rds.amazonaws.com",
    port      = '5432')
    cursor = connection.cursor()
    cursor.execute(sql, (username,))
    result = cursor.fetchall()
    rows=[[i[0]] for i in result]
    connection = None
    return rows

def id_to_title(list):
    '''
    accepting a list of movie ids outputted from the model, this function
    will change those ids to titles
    '''
    sql = f"SELECT title FROM movies WHERE movie_id IN %s"
    connection = psycopg2.connect(
    database  = "postgres",
    user      = "postgres",
    password  = os.getenv('DB_PASSWORD'),
    host      = "movie-rec-scrape.cvslmiksgnix.us-east-1.rds.amazonaws.com",
    port      = '5432')
    cursor = connection.cursor()
    cursor.execute(sql, (list,))
    result = list(cursor.fetchall())
    connection = None
    return result

def connect_to_DB():
    connection = psycopg2.connect(
    database  = "postgres",
    user      = "postgres",
    password  = os.getenv('DB_PASSWORD'),
    host      = "movie-rec-scrape.cvslmiksgnix.us-east-1.rds.amazonaws.com",
    port      = '5432')
    cursor = connection.cursor()
    return cursor


def get_imdb_users():
    '''
    returns a list of all of the unique usernames in the IMDB username column
    '''
    cursor = connect_to_DB()
    query = f"SELECT DISTINCT username From reviews"
    cursor.execute(query)
    result = list(cursor.fetchall())
    cursor.close()
    users = []
    print("retrieved usernames")
    for name in result:
        users.append(name[0])

    unique_users = set(users)
    unique_users = list(unique_users)
    unique_users.sort()
    return unique_users

def imdb_user_lookup(name):
    '''
    takes in a username and searches the data base for all of the reviews made by that user and
    returns a dataframe.
    '''
    connection = psycopg2.connect(
    database  = "postgres",
    user      = "postgres",
    password  = os.getenv('DB_PASSWORD'),
    host      = "movie-rec-scrape.cvslmiksgnix.us-east-1.rds.amazonaws.com",
    port      = '5432')
    print("connected to database")
    query = f"""SELECT m.primary_title, m.start_year, r.review_date,
       r.user_rating, r.review_title, r.review_text
       FROM movies m
       JOIN reviews r ON m.movie_id = r.movie_id
       WHERE username=%s"""
    try:
        df = pd.read_sql_query(query, connection, params=[name])

        df['review_date'] = pd.to_datetime(df['review_date'])
        df['review_date'] = df['review_date'].dt.strftime('%Y-%m-%d').astype(str)

        df.columns = ['Movie Title','Year Released','Date Reviewed','User Rating',
        'Review Title','Review Text']

        print("values replaced")
        df = df.replace(r'\\n',' ', regex=True) #remove the newlines from the reviews and review titles

        ratings_export=df[['User Rating','Movie Title','Year Released']].copy()
        ratings_export.columns = ['Rating','Name','Year']
        reviews_export=df.filter(['Review Text'],axis=1)
        reviews_export.columns = ['Review']
        return (df, ratings_export, reviews_export)
    except Exception as e:
        print(e)
        return pd.DataFrame(columns=['No User Found!'])


def save_users():
    users = get_imdb_users()
    with open("Usernames.txt","w") as file:
        for user in users:
            file.write(user)
            file.write("\n")

    print(f"saved users to {os.getcwd()}\\Usernames.txt")

def read_users(path):
    users = []
    with open(path,'r') as file:
        users = file.readlines()
    return users
