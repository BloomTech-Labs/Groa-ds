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

# Import the `episode_urls.csv` file
episode_urls = pd.read_csv('episode_urls.csv')
# Save episode_urls in a list
episode_urls_list = episode_urls['episode_url'].tolist()

skipped_episodes = []
# The loop
# For each url of the episode
for url in episode_urls_list:
    # Lists to store the scraped data
    titles = []
    dates = []
    user_names = []
    ratings = []
    reviews = []
    review_dates = []

    # Get the html page
    response = requests.get('https://www.metacritic.com'+url+'/user-reviews', headers=headers)
    # Monitor the loop
    # Pause the loop
    sleep(randint(8,15))
    # Add url to skipped list if response.statuse_code!=200
    if response.status_code != 200:
        skipped_episodes.append(url)
        print('URL Skipped!')
    else:
        # Monitor the url scraped
        print(url, "Status:", response.status_code)

        # Parse the content of the request with BeautifulSoup
        page_html = BeautifulSoup(response.text, 'html.parser')

        # Get the reviews containers
        review_containers = page_html.find_all('div', class_='review pad_top1')

        # If any review_container, get the data
        if review_containers:
            # The title
            title = url.replace('/tv/', '').replace('/', ': ').replace('-', ' ')
            # The release date
            release_date = page_html.find('span', class_='release_date').find('span', class_=None).text
            # Get the data for each review
            for container in review_containers:
                # Add the title to the list
                titles.append(title)
                # Add the release date to the list
                dates.append(release_date)
                # Get the user name and add it to the list
                user_name = container.a.text
                user_names.append(user_name)
                # Get the rating and add it to the list
                rating = container.find('div', class_='left fl').text.replace('\n','')
                rating = int(rating)/2
                ratings.append(rating)
                # Get the review and add it to the list
                if container.find('div', class_='review_body'):
                    review = container.find('div', class_='review_body').text.replace('\n', '')
                    reviews.append(review)
                else:
                    reviews.append(' ')
                # Get the review date and add it to the list
                review_date = container.find('span', class_='date').text
                review_dates.append(review_date)

            # Go to the next page (if any)
            # Runs only if there is a `next` button
            if page_html.find('span', class_='flipper next'):
                # Get the page url
                next_page = page_html.find('span', class_='flipper next').a
                # The while loop runs only if next_page!=None
                while next_page:
                    next_page_url = next_page['href']
                    # Monitor the page scraped
                    print(next_page_url)
                    # Download the next page
                    response = requests.get('https://www.metacritic.com'+next_page_url, headers=headers)
                    # Monitor the loop
                    # Pause the loop
                    sleep(randint(8,15))
                    # Throw a warning for non-200 status codes
                    # Add url to skipped list if response.statuse_code!=200
                    if response.status_code != 200:
                        skipped_episodes.append(next_page_url)
                        print('URL Skipped!')
                    # Parse the content of the request with BeautifulSoup
                    page_html = BeautifulSoup(response.text, 'html.parser')
                    # The reviews containers
                    review_containers = page_html.find_all('div', class_='review pad_top1')
                    # The data for each review
                    for container in review_containers:
                        # Add the title to the list
                        titles.append(title)
                        # Add the release date to the list
                        dates.append(release_date)
                        # Get the user name and add it to the list
                        user_name = container.a.text
                        user_names.append(user_name)
                        # Get the rating and add it to the list
                        rating = container.find('div', class_='left fl').text.replace('\n','')
                        rating = int(rating)/2
                        ratings.append(rating)
                        # Get the review and add it to the list
                        if container.find('div', class_='review_body'):
                            review = container.find('div', class_='review_body').text.replace('\n', '')
                            reviews.append(review)
                        else:
                            reviews.append(' ')
                        # Get the review date and add it to the list
                        review_date = container.find('span', class_='date').text
                        review_dates.append(review_date)
                    # Get the page url
                    # The while loop stops if next_page==None
                    next_page = page_html.find('span', class_='flipper next').a

            # Add lists to a dataframe
            episode_ratings = pd.DataFrame({
            'title' : titles,
            'release_date' : dates,
            'user_name' : user_names,
            'rating' : ratings,
            'review' : reviews,
            'review_date' : review_dates
            })

            # Insert data into the database
            tv_reviews_lst = []
            for i in range(len(episode_ratings)):
                tv_reviews_lst.append([titles[i], dates[i], user_names[i], ratings[i], reviews[i], review_dates[i]])
            cursor = connection.cursor()
            step = 100

            for ix in range(0, len(tv_reviews_lst), step):
                batch = tv_reviews_lst[ix:ix+step]
                execute_batch(cursor, """
                    INSERT INTO tvshow_reviews (title, release_date, user_name, rating, review_text, review_date)
                    VALUES (%s, %s, %s, %s, %s, %s);
                    """, batch
                )
            cursor.close()
            connection.commit()
            print('DONE!')
        else:
            print('No reviews to add!')

skipped_episodes_df = pd.DataFrame({
    'url':skipped_episodes
})
skipped_episodes_df.to_csv('skipped_episodes.csv', index=False)
    