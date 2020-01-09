import psycopg2
import pandas as pd
from decouple import config

#to do: use decouple to hide the passwords and add to gitignore
def query(username):
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
