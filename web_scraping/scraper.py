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
    database = "postgres",
    user     = "postgres",
    password = getpass(),
    host     = "movie-rec-scrape.cvslmiksgnix.us-east-1.rds.amazonaws.com",
    port     = "5432"
    )

# cursor object
cursor_boi = connection.cursor()

print("Connected!")


def create_log(movie_name, num_review, num_nan, elapsed):
    """
    Creates a log for each movie scraped.

    Takes info generated within imdb_scraper to produce a log file to return
    a log of the movie name, the number of reviews, and the time taken
    """
    path = os.getcwd()
    os.chdir(path)

    # remove punctuation from the movie name
    movie_name = re.sub(r'[^\w\s]', '', movie_name)

    with open('Logfile.txt', 'a+') as file:
        file.write("---------------------------------------------------------------------\n")
        file.write(str(datetime.now()) + "\n")
        file.write(f"Movie Title: {movie_name}\n")
        file.write(f"This movie has {num_review} reviews\n")
        file.write(f"Out of {num_review} reviews there were {num_nan} with NaN ratings\n")
        file.write(f"Finished Scraping {movie_name} in {round(elapsed,2)} seconds\n")
        file.write("----------------------------------------------------------------------")
        file.write("\n")


def imdb_scraper(id_list):
    """
    Scrapes imbd.com for review pages.

    create_log, make_dataframe, and insert_rows are intended to be used inside
    this function. Takes in the id of the movie in "ttxxxxxxx" format, robust
    to different numbers of numerals. Fails gracefully on movies with no
    reviews, moving on without returning anything.
    """
    t = time.perf_counter()
    # DataFrame Columns (not in order)
    movie_id = []
    rating = []
    reviews = []
    titles = []
    username = []
    found_useful_num = []
    found_useful_den = []
    date = []
    iteration_counter = 0  # number of times the while loop has passed

    for id in id_list:
        t1 = time.perf_counter()
        Nan_count = 0
        review_count = 0
        movie_title = ''

        url_short = f'http://www.imdb.com/title/{id}/'
        url_reviews = url_short + 'reviews?ref_=tt_urv'
        # time.sleep(randint(3, 6))
        response = requests.get(url_reviews)
        if response.status_code != 200:
            continue
        soup = BeautifulSoup(response.text, 'html.parser')
        items = soup.find_all(class_='lister-item-content')

        while True:
            if iteration_counter > 8999:
                df = make_dataframe(movie_id, reviews, rating, titles, username,
                               found_useful_num, found_useful_den, date)
                insert_rows(df)
                movie_id = []
                rating = []
                reviews = []
                titles = []
                username = []
                found_useful_num = []
                found_useful_den = []
                date = []
                iteration_counter = 0
            # populate lists
            for item in items:
                review_count += 1
                reviews.append(item.find(class_="text show-more__control").get_text())
                titles.append(item.find(class_="title").get_text())
                username.append(item.find(class_="display-name-link").get_text())
                date.append(item.find(class_="review-date").get_text())
                movie_id.append(int(id.replace("tt", "")))
                found_useful = item.find(class_="actions text-muted").get_text()
                found_useful = found_useful.replace(",", "")
                usefuls = [int(i) for i in found_useful.split() if i.isdigit()]
                found_useful_num.append(usefuls[0])
                found_useful_den.append(usefuls[1])
                try:
                    rating.append(item.find(class_="rating-other-user-rating").find('span').text)
                except:
                    rating.append(11)
                    Nan_count += 1
                # for loop ends here
            # loading more data if there are more than 25 reviews
            load = soup.find(class_='load-more-data')
            iteration_counter += 1
            try:
                key = load['data-key']
                # exists only if there is a "load More" button
            except:
                break  # End the while loop and go to next movie id
            url_reviews = url_short + 'reviews/_ajax?paginationKey=' + key
            # time.sleep(randint(3, 6))
            response = requests.get(url_reviews)
            soup = BeautifulSoup(response.text, 'html.parser')
            items = soup.find_all(class_='lister-item-content')
            # while loop ends here

        # time took to scrape each movie
        t2 = time.perf_counter()
        finish = t2-t1

        # log the movie
        create_log(movie_title, review_count, Nan_count, finish)
        # for loop ends here

    # create DataFrame
    df = make_dataframe(movie_id, reviews, rating, titles, username,
                        found_useful_num, found_useful_den, date)
    df = insert_rows(df)
    print('All done!')


def make_dataframe(movie_id, reviews, rating, titles, username,
                   found_useful_num, found_useful_den, date):
    df = pd.DataFrame(
           {
            'movie_id': movie_id,
            'reviews': reviews,
            'rating': rating,
            'titles': titles,
            'username': username,
            'helpful_num': found_useful_num,
            'helpful_denom': found_useful_den,
            'date': date
            })
    df['date'] = pd.to_datetime(df['date'])
    df['date'] = df['date'].dt.strftime('%Y-%m-%d').astype(str)
    return df


def insert_rows(df):
    # convert rows into tuples
    row_insertions = ""
    for i in list(df.itertuples(index=False)):
        row_insertions += str((str(i.username.replace("'", "").replace('"', '')),
                               i.movie_id,
                               i.date,
                               str(i.reviews.replace("'", "").replace('"', '')),
                               str(i.titles.replace("'", "").replace('"', '')),
                               int(i.rating),
                               i.helpful_num,
                               i.helpful_denom)) + ", "

    # remove hanging comma
    row_insertions = row_insertions[:-2]

    # create SQL INSERT query
    query = """INSERT INTO reviews(username,
                                   movie_id,
                                   review_date,
                                   review_text,
                                   review_title,
                                   user_rating,
                                   helpful_num,
                                   helpful_denom)
                                   VALUES """ + row_insertions + ";"

    # execute query
    cursor_boi.execute(query)
    connection.commit()
    print("Insertion Complete")

    # total time it took to scrape each review
    t3 = time.perf_counter()
    total = t3 - t
    print(f"Scraped {len(id_list)} movies in {round(total,2)} seconds")


id_list = [row for row in df.iloc[:, 1]]
df2 = imdb_scraper(id_list)

# close connection
if connection:
    cursor_boi.close()
    connection.close()
