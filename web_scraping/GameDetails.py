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

# The loop
# For each url of the game
for game in game_urls:
    # Lists to store the scraped data
    urls = []
    names = []
    release_dates = []
    game_platforms = []
    descriptions = []
    developers = []
    genres_list = []
    online_players_list = []

    # Download the page
    response = requests.get('https://www.metacritic.com'+game+'/details', headers=headers)
    # Pause the loop
    sleep(randint(8,15))
    
    # Add url to skipped list if response.statuse_code!=200
    if response.status_code != 200:
        print('URL Skipped!')
        continue
    else:
        # Monitor the url scraped
        print(game, "Status:", response.status_code)

        # Parse the content of the request with BeautifulSoup
        page_html = BeautifulSoup(response.text, 'html.parser')

        # Save the game url
        # It will be used to assign an id for ratings & reviews
        urls.append(game)

        # The name
        name = page_html.h1.text
        names.append(name)

        # The release date
        date_container = page_html.find('li', class_='summary_detail release_data')
        if date_container:
            release_date = date_container.find('span', class_='data').text
            release_dates.append(release_date)
        else:
            release_dates.append(' ')

        # The game platforms
        primary_platform = page_html.find('span', class_='platform').text.replace('\n','').strip()
        platform_container = page_html.find('li', class_='summary_detail product_platforms')
        if platform_container:
            other_platforms = platform_container.find('span', class_='data').text.replace('\n', '').replace(' ','')
            platforms = [primary_platform+','+other_platforms]
            game_platforms.append(platforms)
        else:
            game_platforms.append(' ')

        # The description
        summary_container = page_html.find('div', class_='summary_detail product_summary')
        if summary_container:
            description = summary_container.find('span', class_='data').text
            descriptions.append(description)
        else:
            descriptions.append(' ')

        # Developer, genres, and number of online players
        details_container = page_html.find_all('div', class_='product_details')[1]
        if details_container:
            details_values = details_container.find_all('td')
            try:
                column = details_container.find_all('th')[1].text
                if column == 'Developer:':
                    developer = details_values[1].text
                    developers.append(developer)
                else:
                    developers.append(' ')
            except:
                developers.append(' ')
            try:
                column = details_container.find_all('th')[2].text
                if column == 'Genre(s):':
                    genres = details_values[2].text.replace('\r\n', '').replace(' ', '')
                    genres_list.append(genres)
                else:
                    genres_list.append(' ')
            except:
                genres_list.append(' ')
            try:
                column = details_container.find_all('th')[3].text
                if column == 'Number of Online Players:':
                    online_players = details_values[3].text
                    online_players_list.append(online_players)
                else:
                    online_players_list.append(' ')
            except:
                online_players_list.append(' ')
        else:
            developers.append(' ')
            genres_list.append(' ')
            online_players_list.append(' ')

        # Store into a dataframe
        games = pd.DataFrame({
            'url' : urls,
            'name' : names,
            'release_date' : release_dates,
            'platforms' : game_platforms,
            'description' : descriptions,
            'developer' : developers,
            'genres' : genres_list,
            'number_online_players' : online_players_list
        })

        # Insert data into the database
        games_lst = []
        for i in range(len(games)):
            games_lst.append([urls[i], names[i], release_dates[i], game_platforms[i], descriptions[i], developers[i], genres_list[i], online_players_list[i]])
        cursor = connection.cursor()
        step = 10

        for ix in range(0, len(games_lst), step):           
            batch = games_lst[ix:ix+step]
            execute_batch(cursor, """
                INSERT INTO games (url, name, release_date, platforms, description, developer, genres, num_online_players)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
                """, batch
            )
        cursor.close()
        connection.commit()
        print('DONE!')