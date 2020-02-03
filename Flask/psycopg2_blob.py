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
    cursor = connect_to_DB()
    print("connected to database")
    query = f"SELECT * From reviews WHERE username='{name}'"
    cursor.execute(query)
    results = cursor.fetchall()
    cursor.close()
    print("connection closed")
    movie_id = []
    date = []
    rating = []
    username = []
    review = []
    title = []
    for result in results:
        movie_id.append(result[0])
        date.append(result[1])
        rating.append(result[2])
        username.append(str(result[5])) 
        review.append(result[6])
        title.append(result[7])
    
    print("Lists created")
    

    df = pd.DataFrame(
            {
                'movie_id': movie_id,
                'reviews': review,
                'rating': rating,
                'titles': title,
                'username': username,
                'date': date
                })

    title = pd.read_csv('title_basics_small.csv')
    title.drop(['primaryTitle','startYear'],axis = 1,inplace = True)
    match = title.to_dict()
    

    # theres probably a faster way to do this part but for now this will have to do
    ################################################################################
    movie_ids = df["movie_id"].tolist()                                            
    for id in movie_ids:
        try:
            value = match['originalTitle'][int(id)]
            #print(id,value)
            df.replace(to_replace = int(id),value = value,inplace = True)
        except:
            continue
    ################################################################################

    df['date'] = pd.to_datetime(df['date'])
    df['date'] = df['date'].dt.strftime('%Y-%m-%d').astype(str)
    print("values replaced")
    return df
     

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

#name = "SnoopyStyle"
#df = imdb_user_lookup(name)
#print(df.head(10))



