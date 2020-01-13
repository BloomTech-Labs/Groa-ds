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
import datetime
from collections import Counter



class Update():
    '''
    The goal for this class is to pull in new reviews that are not yet in the database.

    This will be achieved by:
        - pull all the review IDs from the database and store in a list
        - use the movie IDs from the database and sort the reviews by most recent
        - if the first revie ID isnt in the data base go on to the next review
        - once theres a review that is in the database, stop and go to the next movie ID

    
                            ########################## Methods ############################

    __init__:
        class setup method that will take in 3 numbers in dd/mm/yyyy format and will be used as the
        cutoff date for each instance of the class.

    scan:
        Will use a list of movie IDs and the cutoff date to pull each review made after the cutoff date, for each movie ID.
        This function returns a dictionary of review IDs as the keys and the actual review as the value.

    check:
        Takes in a dictionary {'review_id': review text} and checks if the review ID exist in the database. If it does it'll ignore the
        review and go to the next one, otherwise it'll add the review to the database.

    
    
    '''

    def __init__(self,pw):
        self.database = "postgres"
        self.user = "postgres"
        self.password = pw
        self.host = "movie-rec-scrape.cvslmiksgnix.us-east-1.rds.amazonaws.com"
        self.port = "5432"

    def set_date_cutoff(self,day,month,year):

        self.day = day
        self.month = month
        self.year = year
        self.decode = {
            'January':1,
            'February':2,
            'March':3,
            'April':4,
            'May':5,
            'June':6,
            'July':7,
            'August':8,
            'September':9,
            'October':10,
            'November':11,
            'December':12
        }
        
    def connect_to_database(self):
        """
        Connects to the database and returns a cursor.
        """
        connection = psycopg2.connect(
            database = self.database,
            user     = self.user,
            password = self.password,
            host     = self.host,
            port     = self.port
            )
        return connection.cursor()

    def pull_ids(self,save = True,filename = False):
        '''
        Connects to the database and retrieves the all of the review ids and returns it as a list
        '''
        self.start_timer()
        try:
            # connect to the database and qurey the data base for the review/movie id
            cursor = self.connect_to_database()
            query = "SELECT review_id, movie_id FROM reviews"
            cursor.execute(query)

            # put all of the review/movie ids into a list (a list of tuples)
            self.ids = cursor.fetchall()
            cursor.close()
         
            
        
        except Exception as e:
            print(e)
        
        elapsed = self.end_timer()
        elapsed = self.convert_time(elapsed)

        self.start_timer()
        # save the IDs to a file
        if save:
            # if you pass in a filename, use that otherwise use the default
            filename = input("Enter a filename: ") if filename else "review_ids.csv"

            with open(filename,'w') as file:
                for rev,mov in self.ids:
                    #print(type(rev))
                    #print(rev[:5])
                    #print(mov[:5])
                    file.write(str(rev + "," + mov) + "\n")

            finished = self.end_timer()
            finish = self.convert_time(finished)
            self.load_path = os.path.join(os.getcwd(),filename)
            print(f"File saved to {self.load_path} and was saved in {finish}")

           

        print(f"Retrieved {cursor.rowcount} review/movie ID's in {elapsed}")
        print(f"The ID's are stored as {type(self.ids)}")
        print(f"The first 10 entries are:\n{self.ids[:10]}")
        print()        

        return self.ids

    def start_timer(self):
        self.start = time.perf_counter()

    def end_timer(self):
        self.end = time.perf_counter()
        self.elapsed = self.end - self.start
        return self.elapsed

    def convert_time(self,elapsed):
        e = str(datetime.timedelta(seconds=elapsed))
        return e

    def update(self,ids = None):
        '''
        This function takes in the list of review/movie ids and splits them into their 
        own lists. 
        
        Process:

        1) Each unique movie ID is used to search IMBd for its movie, and the reviews 
        are sorted by recency.
        
        2) The top review will have its ID checked against review IDs in the
        database to see if there is a match. 
        
        3) If there isn't a match (meaning that the review ID is not yet
        in the list of review IDs) that review will be saved and step 2 will be repeated with the next
        review on the page. 

        4) Once the function comes across a review with its review ID already in the database, it will
        be the last review scraped for that movie ID and the whole process is repeated with the next unique
        movie ID.

        '''

        
        ids = self.ids if ids is None else ids
        review_ids = []
        movie_ids = []

        # seperate reviews and movies
        for rid,mid in ids:
            review_ids.append(str(rid))
            movie_ids.append(str(mid))
        
        
        # only unique movie ids
        unique_movie_ids = set(movie_ids)
        unique_movie_ids = list(unique_movie_ids)
        unique_movie_ids.sort()

        print(f"There are {len(unique_movie_ids)} unique movie IDs")
        print(f"The first 10 unique IDs are: \n{unique_movie_ids[:10]}\n")

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

        for id in unique_movie_ids[:10]:
            try:
                self.start_timer()
                id = "tt" + id

                url_short = f'http://www.imdb.com/title/{id}/'

                # sort the reviews by date
                url_reviews = url_short + 'reviews?sort=submissionDate&dir=desc&ratingFilter=0'
                #time.sleep(randint(3, 6))
                response = requests.get(url_reviews)
                if response.status_code != 200:
                        continue
                soup = BeautifulSoup(response.text, 'html.parser')
                items = soup.find_all(class_='lister-item-content')
                print(id)
                

                while True:
                    for item in items:
                    
                        # get the review ID
                        raw_revid = (item.find(class_="title").get("href"))
                        match = re.search(r'rw\d+', raw_revid)
                        review_id = match.group()
                        print(f"review ID from IMBd: {review_id}")

                        # check whether or not the review ID is in the database
                        #if review_id not in review_ids:

                            
                        
                    
                    print("---------------------\n")



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
                    #time.sleep(randint(3, 6))
                    response = requests.get(url_reviews)
                    soup = BeautifulSoup(response.text, 'html.parser')
                    items = soup.find_all(class_='lister-item-content')
                    # while loop ends here
                

            except:
                pass
        
    def show(self,lst):
        '''
        Outputs any list in a formatted output.
        '''
        for count,index in enumerate(lst):
            print(f"{count+1}) {index}")

    def load_ids(self,path = None):

        path = self.load_path if path is None else path

        df = pd.read_csv(path,header = None)
        self.ids = df.values.tolist()
        return self.ids




              

# setup

pw = input("Enter the password: ")
u = Update(pw)
pull = input("Are you pulling new IDs (y/n): \n")
pull = pull.lower()

# Asks if you would like to pull review/movie IDs from the data base
if pull == "y" or pull == "yes":

    # if you are pulling, would you like to save them to a file for faster retrieval (debugging purposes)
    saved = input("Do you want to save this pull to a file (y/n)? \n")

    # yes means that the IDs will be saved to a file and the file will be automatically read to load the IDs
    if saved == "y" or saved == "yes":
        load = True
        u.pull_ids()

    # no means that the IDs are stored in a list and the class will use the list instead
    # unless a file already exist with the IDs on it
    else: 
        load = input("Is there a file that already exist with the IDs (y/n)? \n")
        load = load.lower()
        ids = u.pull_ids(save = False)

    # if the IDs were saved to a file before the program was termintated, load the IDs and start updating the database
    if load == True:
        u.load_ids()
        u.update()
    elif load == "y" or load == "yes":
        path = input("Enter the filename or file path: \n")
        ids = u.load_ids(path = path)
        u.update(ids = ids)
    elif load == "n" or load == "no":
        print("Moving on with the ID's stored in memory")
        u.update(ids = ids) 

else:
    load = input("Is there a file that already exist with the IDs (y/n)? \n")
    if load == "y" or load == "yes":
        path = input("Enter the filename or file path: \n")
        ids = u.load_ids(path = path)
        u.update(ids = ids)
    else:
        print("There are no review/movie IDs in memory or saved to a file.")
    

#ids = u.load_ids(path = "D:\\Documents\\Atom\\review_ids.csv")
#u.update(ids = ids)
