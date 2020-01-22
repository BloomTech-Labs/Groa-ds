import requests
from bs4 import BeautifulSoup
from decouple import config
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
from datetime import timedelta
import sys


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

    def __init__(self,start,end,max_iter, scraper_instance):
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
        self.password = config("PASSWORD")
        self.host = config("HOST")
        self.port = config("PORT")
        self.filename = config("FILENAME")

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

    def get_ids(self):
        '''
        Takes in the names of a file or path to a file to read into a dataframe.
        '''
        df = pd.read_csv(self.filename,encoding = 'ascii',header = None)

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
        directory = os.getcwd()
        os.chdir(directory)

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
# PUT THIS BACK IN
                # time.sleep(randint(3, 6))
                response = requests.get(url_reviews)
                if response.status_code != 200:
                        response = requests.get(url_reviews)
                        if response.status_code != 200:
                            print(f"call to {url_reviews} failed with status code {response.status_code}!")
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
                        except Exception:
                            review_id.append('')
                        try:
                            rating.append(item.find(class_="rating-other-user-rating").find('span').text)
                        except Exception:
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
                    except Exception:
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

    def pull_ids(self,save = True,filename = False):
        '''
        Connects to the database and retrieves the all of the review ids and returns it as a list
        '''
        self.start_timer()
        print("Connecting to database...")
        try:
            # connect to the database and qurey the data base for the review/movie id
            cursor,_ = self.connect_to_database()
            print("Connected.")
            query = "SELECT review_id, movie_id FROM reviews"
            cursor.execute(query)

            # put all of the review/movie ids into a list (a list of tuples)
            print("Fetching IDs...")
            self.ids = cursor.fetchall()
            cursor.close()
            print("Done.")



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

            # class variable used to load the file before program is terminated
            self.load_path = os.path.join(os.getcwd(),filename)
            print(f"File saved to {self.load_path} and was saved in {finish}")



        print(f"Retrieved {cursor.rowcount} review/movie ID's in {elapsed}")
        print(f"The ID's are stored as {type(self.ids)}")
        print(f"The first 10 entries are:\n{self.ids[:10]}")
        print()

        return self.ids

    def start_timer(self):
        """
        starts a timer
        """
        self.start = time.perf_counter()

    def end_timer(self):
        '''
        ends the timer started by start_timer()

        '''
        self.end = time.perf_counter()
        self.elapsed = self.end - self.start
        return self.elapsed

    def convert_time(self,elapsed):
        '''
        converts seconds in to
        HH:MM:SS format
        '''
        e = str(timedelta(seconds=elapsed))
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


        # only unique movie
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
        new_review_id = []
        iteration_counter = 0
        broken = []
        self.start_timer()

        # Start the process described
        print("Updating...")
        for id in unique_movie_ids[:1000]:
            try:
                Nan_count = 0
                review_count = 0
                movie_title = ''
                num = id
                id = "tt" + id

                url_short = f'http://www.imdb.com/title/{id}/'

                # sort the reviews by date
                url_reviews = url_short + 'reviews?sort=submissionDate&dir=desc&ratingFilter=0'
# PUT THIS BACK IN
                #time.sleep(randint(3, 6))
                response = requests.get(url_reviews)
                if response.status_code != 200:
                        response = requests.get(url_reviews)
                        if response.status_code != 200:
                            print(f"call to {url_reviews} failed with status code {response.status_code}!")
                            continue
                soup = BeautifulSoup(response.text, 'html.parser')

                # items holds all the HTML for the webpage
                items = soup.find_all(class_='lister-item-content')



                while True:
                    if iteration_counter >= self.max_iter_count:
                        df = self.make_dataframe(movie_id, reviews, rating, titles,
                                                 username, found_useful_num,
                                                 found_useful_den, date, new_review_id)
                        #self.insert_rows(df)
                        movie_id.clear()
                        rating.clear()
                        reviews.clear()
                        titles.clear()
                        username.clear()
                        found_useful_num.clear()
                        found_useful_den.clear()
                        date.clear()
                        new_review_id.clear()
                        iteration_counter = 0
                        df = df.iloc[0:0]

                    for item in items:

                        # get the review ID
                        raw_revid = (item.find(class_="title").get("href"))
                        match = re.search(r'rw\d+', raw_revid)
                        review_id = match.group()
                        #print(f"review ID from IMBd: {review_id}")

                        # check whether or not the review ID is in the database (steps 2 and 3)
                        if review_id not in review_ids:
                            print(f"Updating {id} at index {unique_movie_ids.index(num)} in the database for review ID {review_id}")
                            review_count += 1

                            # populate lists
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
                            match = re.search(r'rw\d+', raw_revid)
                            try:
                                new_review_id.append(match.group())
                            except Exception:
                                new_review_id.append('')
                            try:
                                rating.append(item.find(class_="rating-other-user-rating").find('span').text)
                            except Exception:
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
                    except Exception:
                        break  # End the while loop and go to next movie id
                    url_reviews = url_short + 'reviews/_ajax?paginationKey=' + key
# PUT THIS BACK IN
                    #time.sleep(randint(3, 6))
                    response = requests.get(url_reviews)
                    soup = BeautifulSoup(response.text, 'html.parser')
                    items = soup.find_all(class_='lister-item-content')
                    # while loop ends here

            except Exception as e:
                print(e,"In update function")
                continue

        print("Updated.")
         # create DataFrame
        df = self.make_dataframe(movie_id, reviews, rating, titles, username,
                            found_useful_num, found_useful_den, date, review_id)
        df.drop_duplicates(inplace = True)
# PUT THIS BACK IN
        #self.insert_rows(df)

        elapsed = self.end_timer()
        elapsed = self.convert_time(elapsed)
        print(f"finished in {elapsed}")
        return df

    def load_ids(self,path = None):
        '''
        This function can only be ran before the program is terminated.
        It uses the class variable self.load_path to locate the saved file with the
        review/movie IDs and automatically loads the data from that file back into
        the class variable self.ids.
        '''

        path = self.load_path if path is None else path

        df = pd.read_csv(path,header = None)
        self.ids = df.values.tolist()
        return self.ids

    def scrape_letterboxd(self, id_list = None):
        """
        Scrapes letterboxd.com for review pages.
        """
        id_list = self.current_ids if id_list is None else id_list
        t = time.perf_counter()
        movie_id = []
        rating = []
        reviews = []
        username =[]
        likes = []
        date = []
        review_id = []
        iteration_counter = 0
        broken = []

        for count,id in enumerate(id_list):
            try:
                t1 = time.perf_counter()
                Nan_count = 0
                review_count = 0
                self.locate(id)
                url_initial = f"https://www.letterboxd.com/imdb/{id}"
                initial_response = requests.get(url_initial)
                # Get title here
                title = ""
                try:
                    soup = BeautifulSoup(initial_response.text, 'html.parser')
                    title = soup.find(class_="headline-1 js-widont prettify").get_text()
                    title = title.replace(" ","-").lower()

                except:
                    print(f"Unable to scrape this ID {id}")
                    continue

                url_reviews = f"https://www.letterboxd.com/film/{title}/reviews/by/activity/"
                # initially, I wanted to make this sorted by recency, but if
                # there are fewer than 12 reviews only sorting by popular is
                # available
                time.sleep(randint(3,6))
                response = requests.get(url_reviews)
                if response.status_code != 200:
                        response = requests.get(url_reviews)
                        if response.status_code != 200:
                            print(f"call to {url_reviews} failed with status code {response.status_code}!")
                            continue

                soup = BeautifulSoup(response.text, 'html.parser')
                items = soup.find_all(class_='film-detail')
                print(f"ID: {id} at index {self.all_ids.index(id)}")
                while True:
                    if iteration_counter >= self.max_iter_count:
                        df = self.letterboxd_dataframe()
                        self.letterboxd_insert(df)
                        movie_id.clear()
                        rating.clear()
                        reviews.clear()
                        username.clear()
                        likes.clear()
                        date.clear()
                        review_id.clear()
                        df = df.iloc[0:0]
                        iteration_counter = 0
                    iteration_counter += 1
                    for item in items:
                        body = item.find(class_="body-text -prose collapsible-text")
                        append = body['data-full-text-url']
                        if item.find(class_="reveal js-reveal") or item.find(class_="collapsed-text"):
                            text_url = 'https://www.letterboxd.com' + append
                            fulltext = requests.get(text_url)
                                if fulltext.status_code != 200:
                                    fulltext = requests.get(text_url)
                                    if fulltext.status_code != 200:
                                        print(f"call to {text_url} failed with status code {fulltext.status_code}!")
                                        continue
                            fulltext = re.sub(r'\<[^>]*\>', "", fulltext.text)
                            reviews.append(fulltext)
                        else:
                            reviews.append(body.get_text())
                        review_count += 1
                        movie_id.append(id.replace("tt", ""))
                        review_id.append(append)
                        # TODO strip down to number only


                        # TODO rating
                        rating1 = str(item.find(class_ ="attribution"))
                        rating1 = rating.split(">")
                        span = rating1[1]
                        span = span.split("-")
                        span = span[2].replace('"','')
                        rate = int(span)
                        rating.append(rate)



                        date.append(item.find(class_="_nobr").get_text())
                        username.append(item.find(class_="name").get_text())
                        likes.append(item.find(class_="svg-action -like cannot-like ").get_text())

                    # TODO looping over multiple pages
                    page_count = 1
                    page_count += 1
                    if soup.find('a', class_="next"):
                        url_more = url_reviews + 'page/' + page_count + '/'
                        response = requests.get(url_more)
                        if response.status_code != 200:
                            response = requests.get(url_more)
                            if response.status_code != 200:
                                print(f"call to {url_more} failed with status code {response.status_code}!")
                                continue
                                # Unsure of proper handling here

                    else:
                        break
                    # While loop ends here
                t2 = time.perf_counter()
                finish = t2-t1

                if count == 0 and os.path.exists(f"Logfile{self.scraper_instance}.txt"):
                    os.remove(f"Logfile{self.scraper_instance}.txt")
                self.create_log(id, review_count, Nan_count, finish)
            except Exception as e:
                broken.append(id)
                print(sys.exc_info()[1])
                continue
        #df = self.letterboxd_dataframe()
        #self.letterboxd_insert()

        t3 = time.perf_counter()
        total = t3 - t
        print(f"Scraped {count + 1} movies in {round(total,2)} seconds")

        print('All done!\n')
        print("The following IDs were not scraped succcessfully:")
        self.show(broken)
        return df

    def letterboxd_insert(self, df):
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
                                   int(i.rating),
                                       i.likes,
                                       i.review_id)) + ", "

        # remove hanging comma
        row_insertions = row_insertions[:-2]
        cursor_boi, connection = self.connect_to_database()
        # create SQL INSERT query
        query = """INSERT INTO letterboxd_reviews(username,
                                                  movie_id,
                                                  review_date,
                                                  review_text,
                                                  user_rating,
                                                  likes,
                                                  review_id)
                                                  VALUES """ + row_insertions + ";"

        # execute query
        cursor_boi.execute(query)
        connection.commit()
        cursor_boi.close()
        connection.close()
        print("Insertion Complete")

def checker(str):
    """
    Quick utility function to help with our input Q&A
    """
    valid_inputs = ['y', 'yes', 'n', 'no']
    var = input(str).lower()
    while var in valid_inputs == False:
        print("That's not a valid input!")
        var = input(str).lower()
    return var

'''if __name__ == "__main__":

    start = int(input("Start at which row? "))
    end = int(input("End at which row? ")) + 1
    if start > end:
        raise ValueError("The starting position needs to be less than or equal to end position.")

    max_iter = int(input("Maximum iterations? "))
    if max_iter < 1:
        raise ValueError("Maximum iterations must be positive.")

    scraper_instance = input("Which scraper instance is this? ")
    s = Scraper(start,end,max_iter,scraper_instance)

    mode = checker("Are you starting a new database (y/n): \n")
    if mode == "y" or mode == "yes":
        ids = s.get_ids()
        df = s.scrape(ids)
    elif mode == "n" or mode == "no":
        pull = checker("Are you pulling new IDs (y/n): \n")

        # Asks if you would like to pull review/movie IDs from the data base
        if pull == "y" or pull == "yes":

            # if you are pulling, would you like to save them to a file for faster retrieval (debugging purposes)
            saved = checker("Do you want to save this pull to a file (y/n)? \n")

            # yes means that the IDs will be saved to a file and the file will be automatically read to load the IDs
            if saved == "y" or saved == "yes":
                load = True
                s.pull_ids()

            # no means that the IDs are stored in a list and the class will use the list instead
            # unless a file already exist with the IDs on it
            elif saved == 'n' or saved == 'no':
                load = checker("Is there a file that already exist with the IDs (y/n)? \n")
                ids = s.pull_ids(save = False)

            # if the IDs were saved to a file before the program was termintated, load the IDs and start updating the database
            if load == True:
                s.load_ids()
                df = s.update()

                # if there is already a file that exist, use that file
            elif load == "y" or load == "yes":
                path = input("Enter the filename or file path: \n")
                try:
                    ids = s.load_ids(path = path)
                    df = s.update(ids = ids)
                except Exception:
                    raise ValueError("File Not Found")

                # if a file doesn't exist it will use the IDs already in memory
            elif load == "n" or load == "no":
                print("Moving on with the ID's stored in memory")
                df = s.update(ids = ids)

        # you don't want to pull new reviews
        else:
            # but there is a file that already contains the IDs needed
            load = checker("Is there a file that already exist with the IDs (y/n)? \n")
            if load == "y" or load == "yes":
                path = input("Enter the filename or file path: \n")
                try:
                    ids = s.load_ids(path = path)
                    df = s.update(ids = ids)
                except Exception:
                    raise ValueError("File Not Found")
            else:
                print("There are no review/movie IDs in memory or saved to a file.")'''

s = Scraper(0,10,5,1)
ids = s.get_ids()
s.scrape_letterboxd(id_list=ids)
