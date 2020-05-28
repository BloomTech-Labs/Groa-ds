import os
import pandas as pd
import psycopg2
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from psycopg2.extras import execute_batch
from random import randint
from time import sleep

# Load .env file
load_dotenv()

DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
PORT = os.getenv("PORT")
HOST = os.getenv("HOST")
headers = os.getenv("headers")

# Connect to the database
connection = psycopg2.connect(
    user=DB_USER,
    password=DB_PASSWORD,
    host=HOST,
    port=PORT,
    database=DB_NAME
)

# Import the `game_urls.csv` file
game_urls = pd.read_csv('game_urls.csv')
game_urls = game_urls['url'].tolist()

skipped_urls = []
# The loop
# For each url of the game
for game in game_urls:
    # Lists to store the scraped data
    urls = []
    user_names = []
    ratings = []
    reviews = []
    review_dates = []

    # Download the page
    response = requests.get('https://www.metacritic.com'+game+'/user-reviews', headers=headers)
    # Pause the loop
    sleep(randint(8,15))

    # Add url to skipped list if response.statuse_code!=200
    if response.status_code != 200:
        skipped_urls.append(game)
        print('URL Skipped!')
    else:
        # Monitor the url scraped
        print(game, "Status:", response.status_code)
        # Parse the content of the request with BeautifulSoup
        page_html = BeautifulSoup(response.text, 'html.parser')

        # Reviews section
        all_reviews = page_html.find('ol', class_='reviews user_reviews')
        # If there is a user reviews section
        if all_reviews:
            # The users
            all_users = all_reviews.find_all('div', class_='name')
            for i in range(len(all_users)):
                user_names.append(all_users[i].text.replace('\n', ''))
                # Save the game url
                urls.append(game)

            # The ratings
            all_ratings = all_reviews.find_all('div', class_='review_grade')
            for i in range(len(all_ratings)):
                rating = all_ratings[i].text.replace('\n', '')
                rating = int(rating)/2
                ratings.append(rating)

            # The reviews
            all_user_reviews = all_reviews.find_all('div', class_='review_body')
            for i in range(len(all_user_reviews)):
                if all_user_reviews[i].span:
                    review = all_user_reviews[i].span.text
                    reviews.append(review)
                else:
                    reviews.append(' ')

            # The review dates
            all_dates = all_reviews.find_all('div', class_='date')
            for i in range(len(all_dates)):
                review_date = all_dates[i].text
                review_dates.append(review_date)
            
            # Go to the next page
            # If there is a next button
            if page_html.find('span', class_='flipper next'):
                # Get the reference of the next page button
                next_page = page_html.find('span', class_='flipper next').a
                # Loop through the next pages while the button has a reference
                while next_page:
                    # Next page url
                    next_page_url = next_page['href']
                    # Download the page
                    response = requests.get('https://www.metacritic.com'+next_page_url, headers=headers)
                    # Pause the loop
                    sleep(randint(8,15))
                    # Add url to skipped list if response.statuse_code!=200
                    if response.status_code != 200:
                        skipped_urls.append(game)
                        print('URL Skipped!')
                    else:
                        # Monitor the url scraped
                        print(next_page_url, "Status:", response.status_code)

                        # Parse the content of the request with BeautifulSoup
                        page_html = BeautifulSoup(response.text, 'html.parser')

                        # Reviews section
                        all_reviews = page_html.find('ol', class_='reviews user_reviews')

                        # If there is a user reviews section
                        if all_reviews:
                            # The users
                            all_users = all_reviews.find_all('div', class_='name')
                            for i in range(len(all_users)):
                                user_names.append(all_users[i].text.replace('\n', ''))
                                # Save the game url
                                urls.append(game)

                            # The ratings
                            all_ratings = all_reviews.find_all('div', class_='review_grade')
                            for i in range(len(all_ratings)):
                                rating = all_ratings[i].text.replace('\n', '')
                                rating = int(rating)/2
                                ratings.append(rating)

                            # The reviews
                            all_user_reviews = all_reviews.find_all('div', class_='review_body')
                            for i in range(len(all_user_reviews)):
                                if all_user_reviews[i].span:
                                    review = all_user_reviews[i].span.text
                                    reviews.append(review)
                                else:
                                    reviews.append(' ')

                            # The review dates
                            all_dates = all_reviews.find_all('div', class_='date')
                            for i in range(len(all_dates)):
                                review_date = all_dates[i].text
                                review_dates.append(review_date)

                        # Get the next page
                        # The while loop stops if next_page==None
                        if page_html.find('span', class_='flipper next'):
                            next_page = page_html.find('span', class_='flipper next').a
                        else:
                            next_page=None
        
            # Store into a dataframe
            game_reviews = pd.DataFrame({
                'url' : urls,
                'user_name' : user_names,
                'rating' : ratings,
                'review' : reviews,
                'review_date' : review_dates
            })

            # Insert data into the database
            game_reviews_lst = []
            for i in range(len(game_reviews)):
                game_reviews_lst.append([urls[i], user_names[i], ratings[i], reviews[i], review_dates[i]])
            cursor = connection.cursor()
            step = 100

            for ix in range(0, len(game_reviews_lst), step):           
                batch = game_reviews_lst[ix:ix+step]
                execute_batch(cursor, """
                    INSERT INTO game_reviews (url, user_name, rating, review, review_date)
                    VALUES (%s, %s, %s, %s, %s);
                    """, batch
                )
            cursor.close()
            connection.commit()
            print('DONE!')
        else:
            print('No reviews to add!')

# Save skipped urls
skipped_urls_df = pd.DataFrame({
    'url':skipped_urls
})
skipped_urls_df.to_csv('SkippedGameReviews.csv', index=False)