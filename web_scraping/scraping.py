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

class Scraper():

    def __init__(self):
        self.current_ids = []
        self.all_ids = []
        self.range = 0
        self.pickup = 0
        pass

    def get_ids(self,path,start,end):
        '''
        takes in the names of a file or path to a file to read into a dataframe
        '''

        df = pd.read_csv(path,encoding = 'ascii')

        # get all the rows from the second column and then select only the ones from the start and end positions
        id_list = [row for row in df.iloc[:,1]]
        self.all_ids = id_list

        id_list = id_list[start:end]
        self.current_ids = id_list
        
        # lets the class know the range of ID's its grabbing at a time
        if start > end:
            raise ValueError("The start position needs to be less than the end position")
        self.range = abs(end - start)

        return id_list

    def show(self,lst):
        '''
        outputs any list in a formatted output
        '''
        for count,index in enumerate(lst):
            print(f"{count+1}) {index}")

    def create_log(self,movie_name, num_review, num_nan, elapsed):
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
    
    def make_dataframe(self,movie_id, reviews, rating, titles, username,
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

    def scrape(self,id_list = None):
        """
        Scrapes imbd.com for review pages.

        create_log, make_dataframe, and insert_rows are intended to be used inside
        this function. Takes in the id of the movie in "ttxxxxxxx" format, robust
        to different numbers of numerals. Fails gracefully on movies with no
        reviews, moving on without returning anything.
        """
        id_list = self.current_ids if id_list is None else id_list

        t = time.perf_counter()
        movie_id = []
        rating = []
        reviews = []
        titles = []
        username = []
        found_useful_num = []
        found_useful_den = []
        date = []
        iteration_counter = 0
        
        for id in id_list:
            t1 = time.perf_counter()
            Nan_count = 0
            review_count = 0
            movie_title = ''
            self.locate(id)

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
                    df = self.make_dataframe(movie_id, reviews, rating, titles, username,
                                found_useful_num, found_useful_den, date)

                    #insert_rows(df)
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
            self.create_log(movie_title, review_count, Nan_count, finish)
            # for loop ends here

        # create DataFrame
        df = self.make_dataframe(movie_id, reviews, rating, titles, username,
                            found_useful_num, found_useful_den, date)

        # this line was causing a return error so i removed it and re-added it without having it assigned to anything                    
        #df = insert_rows(df)
        #insert_rows(df)

        #total time it took to scrape each review
        t3 = time.perf_counter()
        total = t3 - t
        print(f"Scraped {len(id_list)} movies in {round(total,2)} seconds")

        print('All done!')
        return df

    def locate(self,last_id):
        '''
        This function takes in the last id used for scraping and tells you its
        index in the master list of movie ids and the curent ids being used. it also 
        will tell you how many more ids there are left to scrape.
        '''
        self.pickup = self.all_ids.index(last_id)
        



        

s = Scraper()
path = "D:\\Documents\\Atom\\Labs 2019\\movie-recommender\\web_scraping\\movieid_shuffle_small.csv"
start = int(input("Start at which row?"))
end = int(input("End at which row?"))      
ids = s.get_ids(path,start,end)
#s.show(ids)
df = s.scrape(ids)