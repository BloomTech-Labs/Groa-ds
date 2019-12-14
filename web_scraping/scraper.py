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
cursor_boi = connection.cursor()

print("Connected!")

def create_log(movie_name,num_review,num_nan,elapsed):
    # path = "C:\\Documents\\Atom\\Labs 2019\\Movie recommender\\web scraping\\logs"
    path = os.getcwd()
    os.chdir(path)

    # remove punctuation from the movie name
    movie_name = re.sub(r'[^\w\s]','',movie_name)

    with open('Logfile.txt','a+') as file:
        file.write("---------------------------------------------------------------------\n")
        file.write(str(datetime.now()) + "\n")
        file.write(f"Movie Title: {movie_name}\n")
        file.write(f"This movie has {num_review} reviews\n")
        file.write(f"Out of {num_review} reviews there were {num_nan} with NaN ratings\n")
        file.write(f"Finished Scraping {movie_name} in {round(elapsed,2)} seconds\n")
        file.write("----------------------------------------------------------------------")
        file.write("\n")



def imdb_scraper(id_list):
  t = time.perf_counter()
  # DataFrame Columns (not in order)
  index = []
  index_ = 0
  movie_id = []
  rating = []
  reviews = []
  titles = []
  username = []
  found_useful_num = []
  found_useful_den = []
  date = []
  # total_ratings = 0


  for id in id_list:
    t1 = time.perf_counter()
    Nan_count = 0
    review_count = 0
    movie_title = ''
    review_count = 0


    url_short = f'http://www.imdb.com/title/{id}/'
    url_reviews = url_short + 'reviews?ref_=tt_urv'
    # url_ratings = url_short + 'ratings?ref_=tturv_ql_4'



    # Ratings page
    # page = requests.get(url_ratings)
    # content = BeautifulSoup(page.content, 'html.parser')
    #
    # total_ratings = list(content.find(class_ = "allText"))
    # total_ratings = total_ratings[0]
    # total_ratings = re.findall(r'[0-9]+', total_ratings)
    # total_ratings = ''.join(total_ratings)

    response = requests.get(url_reviews)
    soup = BeautifulSoup(response.text, 'html.parser')
    items = soup.find_all(class_='lister-item-content')
    try:
        movie_title = (soup.find(class_ = "subnav_heading").get_text())
    except:
        pass

    while True:

      # populate lists
      for item in items:
          review_count += 1
          reviews.append(item.find(class_ = "text show-more__control").get_text())
          titles.append(item.find(class_ = "title").get_text())
          username.append(item.find(class_ = "display-name-link").get_text())
          date.append(item.find(class_ = "review-date").get_text())
          movie_id.append(int(id.replace("tt", "")))
          found_useful = item.find(class_ = "actions text-muted").get_text()
          found_useful = found_useful.replace(",", "")
          usefuls = [int(i) for i in found_useful.split() if i.isdigit()]
          found_useful_num.append(usefuls[0])
          found_useful_den.append(usefuls[1])
          index.append(index_)
          index_ += 1
          try:
              rating.append(item.find(class_="rating-other-user-rating").find('span').text)
          except:
              rating.append(11)
              Nan_count += 1

      # loading more data
      load = soup.find(class_='load-more-data')
      try:
        key = load['data-key']
      except:
        break
      url_reviews = url_short + '/reviews/_ajax?paginationKey=' + key

      response = requests.get(url_reviews)
      soup = BeautifulSoup(response.text, 'html.parser')
      items = soup.find_all(class_='lister-item-content')

    # time took to scrape each movie
    t2 = time.perf_counter()
    finish = t2-t1

    # log the movie
    create_log(movie_title,review_count,Nan_count,finish)

  # create DataFrame
  df = pd.DataFrame(
        {
            'index':index,
            'movie_id':movie_id,
            'review':reviews,
            'rating':rating,
            'title':titles,
            'username':username,
            'helpful_num':found_useful_num,
            'helpful_denom':found_useful_den,
            'date':date
            # 'no. of ratings':total_ratings
        })

  # convert date column into date object
  df['date'] = pd.to_datetime(df['date'])
  df['date'] = df['date'].dt.strftime('%Y-%m-%d').astype(str)

  # convert rows into tuples
  row_insertions = ""
  for i in list(df.itertuples(index=False)):
      row_insertions += str((i.index,
                                    i.username,
                                    i.movie_id,
                                    i.date,
                                    str(i.review.replace("'", "").replace('"', '')),
                                    str(i.title.replace("'", "").replace('"', '')),
                                    int(i.rating),
                                    i.helpful_num,
                                    i.helpful_denom)) + ", "

  # remove hanging comma
  row_insertions = row_insertions[:-2]

  # create SQL INSERT query
  query = """INSERT INTO reviews(review_id,
                                username,
                                movie_id,
                                review_date,
                                review_text,
                                review_title,
                                user_rating,
                                helpful_num,
                                helpful_denom)
                                VALUES """ + row_insertions + ";"
  # simple test query
  test_query = """INSERT INTO reviews(review_id, username, movie_id, review_date, review_text, review_title, user_rating, helpful_num, helpful_denom) VALUES (1, 'coop', 12345678, '2016-06-23', 'I love this movie!', 'Me happy', 5, 6, 12 )"""

  # execute query
  cursor_boi.execute(query)
  connection.commit()
  print(query)

  # total time it took to scrape each review
  t3 = time.perf_counter()
  total = t3 - t
  print(f"Scraped {len(id_list)} movies in {round(total,2)} seconds")

  return df


id_list = [row for row in df.iloc[:1000, 1]]
df2 = imdb_scraper(id_list)
# print(df.head())

# close connection
if connection:
    cursor_boi.close()
    connection.close()
