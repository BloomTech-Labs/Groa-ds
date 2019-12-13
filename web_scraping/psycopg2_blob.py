import psycopg2
from getpass import getpass

# connect to database
connection = psycopg2.connect(
    database  = "postgres",
    user      = "postgres",
    password  = getpass(),
    host      = "movie-rec-scrape.cvslmiksgnix.us-east-1.rds.amazonaws.com",
    port      = '5432'
)

#cursor object
cursor_boi = connection.cursor()

# simple test query
test_query = """INSERT INTO reviews (review_id, username, movie_id, review_date, review_text, review_title, user_rating, helpful_num, helpful_denom) VALUES (1, 'coop', 12345678, '2016-06-23', 'I love this movie!', 'Me happy', 5, 6, 12 )"""

# execute query
cursor_boi.execute(test_query)
print(test_query)

# close connection
if(connection):
    cursor_boi.close()
    connection.close()
