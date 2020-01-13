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
"""
Scrapes IMDB and contains utility and logging functions.

Start and end parameters are inclusive. max_iter controls how many loops
can be run before the program inserts into the database. scraper_instance must
be different for each instance of the program to ensure their log files do not
mess each other up. pw is currently taken from getpass and is the password
for the postgres database.

TODO: change pw and path to environment variables
Make a scraper that will only grab reviews that the database does not already
have.
Make the scraper automatically restart itself.
"""
    def __init__(self,start,end,max_iter, scraper_instance, pw):
        self.start = start
        self.end = end
        self.current_ids = []
        self.all_ids = []
        self.range = 0
        self.pickup = 0
        self.max_iter_count = max_iter
        self.scraper_instance = scraper_instance
        self.database = "postgres"
        self.user = "postgres"
        self.password = pw
        self.host = "movie-rec-scrape.cvslmiksgnix.us-east-1.rds.amazonaws.com"
        self.port = "5432"

    def connect_to_database(self):
        """
        Connects to the database.
        """
        connection = psycopg2.connect(
            database = self.database,
            user     = self.user,
            password = self.password,
            host     = self.host,
            port     = self.port
            )
        return connection.cursor(), connection

    def get_ids(self,path):
        '''
        Takes in the names of a file or path to a file to read into a dataframe.
        '''
        df = pd.read_csv(path,encoding = 'ascii',header = None)

        # get all the rows from the second column and then select only the ones from the start and end positions
        id_list = [row for row in df.iloc[:,1]]
        self.all_ids = id_list

        id_list = id_list[self.start:self.end]
        self.current_ids = id_list

        # lets the class know the range of ID's its grabbing at a time
        if self.start > self.end:
            raise ValueError("The start position needs to be less than the end position")
        self.range = abs(self.end - self.start)

        return id_list

    def show(self,lst):
        '''
        Outputs any list in a formatted output.
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

        with open(f'Logfile{self.scraper_instance}.txt', 'a+') as file:
            file.write("---------------------------------------------------------------------\n")
            file.write(str(datetime.now()) + "\n")
            file.write(f"Movie ID: {movie_name}\n")
            file.write(f"This movie has {num_review} reviews\n")
            file.write(f"Out of {num_review} reviews there were {num_nan} with NaN ratings\n")
            file.write(f"Finished Scraping {movie_name} in {round(elapsed,2)} seconds\n")
            file.write("----------------------------------------------------------------------")
            file.write("\n")

    def make_dataframe(self,movie_id, reviews, rating, titles, username,
                   found_useful_num, found_useful_den, date, review_id):
        df = pd.DataFrame(
            {
                'movie_id': movie_id,
                'reviews': reviews,
                'rating': rating,
                'titles': titles,
                'username': username,
                'helpful_num': found_useful_num,
                'helpful_denom': found_useful_den,
                'date': date,
                'review_id': review_id
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
        review_id = []
        iteration_counter = 0
        broken = []

        for count,id in enumerate(id_list):
            try:
                t1 = time.perf_counter()
                Nan_count = 0
                review_count = 0
                movie_title = ''
                self.locate(id)

                url_short = f'http://www.imdb.com/title/{id}/'
                url_reviews = url_short + 'reviews?ref_=tt_urv'
                time.sleep(randint(3, 6))
                response = requests.get(url_reviews)
                if response.status_code != 200:
                        continue
                soup = BeautifulSoup(response.text, 'html.parser')
                items = soup.find_all(class_='lister-item-content')
                print(f"ID: {id} at index {self.all_ids.index(id)}")
                while True:

                    if iteration_counter >= self.max_iter_count:
                        df = self.make_dataframe(movie_id, reviews, rating, titles,
                                                 username, found_useful_num,
                                                 found_useful_den, date, review_id)
                        self.insert_rows(df)
                        movie_id.clear()
                        rating.clear()
                        reviews.clear()
                        titles.clear()
                        username.clear()
                        found_useful_num.clear()
                        found_useful_den.clear()
                        date.clear()
                        review_id.clear()
                        iteration_counter = 0
                        df = df.iloc[0:0]

                    # populate lists
                    for item in items:
                        review_count += 1
                        reviews.append(item.find(class_="text show-more__control").get_text())
                        titles.append(item.find(class_="title").get_text())
                        username.append(item.find(class_="display-name-link").get_text())
                        date.append(item.find(class_="review-date").get_text())
                        movie_id.append(id.replace("tt", ""))
                        found_useful = item.find(class_="actions text-muted").get_text()
                        found_useful = found_useful.replace(",", "")
                        usefuls = [int(i) for i in found_useful.split() if i.isdigit()]
                        found_useful_num.append(usefuls[0])
                        found_useful_den.append(usefuls[1])
                        raw_revid = (item.find(class_="title").get("href"))
                        match = re.search('rw\d+', raw_revid)
                        try:
                            review_id.append(match.group())
                        except:
                            review_id.append('')
                        try:
                            rating.append(item.find(class_="rating-other-user-rating").find('span').text)
                        except:
                            rating.append(11)
                            Nan_count += 1
                        # for loop ends here
                    # loading more data if there are more than 25 reviews
                    load = soup.find(class_='load-more-data')
                    if items:
                        iteration_counter += 1
                    try:
                        key = load['data-key']
                        # exists only if there is a "load More" button
                    except:
                        break  # End the while loop and go to next movie id
                    url_reviews = url_short + 'reviews/_ajax?paginationKey=' + key
                    time.sleep(randint(3, 6))
                    response = requests.get(url_reviews)
                    soup = BeautifulSoup(response.text, 'html.parser')
                    items = soup.find_all(class_='lister-item-content')
                    # while loop ends here

                # time took to scrape each movie
                t2 = time.perf_counter()
                finish = t2-t1

                # if the logfile exist already within the first iteration
                # it will be deleted and recreated which fixes the issue of
                # duplicating info when ran several times
                if count == 0 and os.path.exists(f"Logfile{self.scraper_instance}.txt"):
                    os.remove(f"Logfile{self.scraper_instance}.txt")

                # log the movie
                self.create_log(id, review_count, Nan_count, finish)
                # for loop ends here

            # catches any error and lets you know which ID was the last one scraped
            except Exception as e:
                broken.append(id) 
                continue

        # create DataFrame
        df = self.make_dataframe(movie_id, reviews, rating, titles, username,
                            found_useful_num, found_useful_den, date, review_id)
        self.insert_rows(df)

        #total time it took to scrape each review
        t3 = time.perf_counter()
        total = t3 - t
        print(f"Scraped {count + 1} movies in {round(total,2)} seconds")

        print('All done!\n')
        print("The following IDs were not scraped succcessfully:")
        self.show(broken)
        return df

    def locate(self,last_id):
        '''
        This function takes in the last id used for scraping and tells you its
        index in the master list of movie ids and the curent ids being used. it
        also will tell you how many more ids there are left to scrape.
        '''
        self.pickup = self.all_ids.index(last_id)

        #writes the last used ID to a file
        with open("pickup.txt",'w') as file:
            file.write(str(self.pickup+1))
            file.write("\n")
            file.write(str(self.end))

    def pick_up(self):
        """
        Currently unused.
        """
        with open(f"pickup{self.scraper_instance}.txt",'r') as file:
            lines = file.readlines()
            self.pickup = lines[0]
            self.end = lines[1]
            self.pickup = int(self.pickup)
            self.end = int(self.end)

    def insert_rows(self, df):
        """
        Connects to the database and inserts reviews as new rows.

        Takes a dataframe and formats it into a very long string to convert to
        SQL. Connects to the database, executes the query, and closes the cursor
        and connection.
        """
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
                                i.helpful_denom,
                                i.review_id)) + ", "

        # remove hanging comma
        row_insertions = row_insertions[:-2]
        cursor_boi, connection = self.connect_to_database()
        # create SQL INSERT query
        query = """INSERT INTO reviews(username,
                                    movie_id,
                                    review_date,
                                    review_text,
                                    review_title,
                                    user_rating,
                                    helpful_num,
                                    helpful_denom,
                                    review_id)
                                    VALUES """ + row_insertions + ";"

        # execute query
        cursor_boi.execute(query)
        connection.commit()
        cursor_boi.close()
        connection.close()
        print("Insertion Complete")

if __name__ = "__main__":
    path = "movieid.csv"
    pw = getpass()
    start = int(input("Start at which row? "))
    end = int(input("End at which row? ")) + 1
    max_iter = int(input("Maximum iterations? "))
    scraper_instance = int(input("Which scraper instance is this? "))
    s = Scraper(start,end,max_iter, scraper_instance, pw)
    ids = s.get_ids(path)
    #s.show(ids)
    df = s.scrape(ids)
