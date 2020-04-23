from bs4 import BeautifulSoup
import sys
import time
from random import randint
import re
import requests
import pandas as pd
from psycopg2.extras import execute_batch


from web_scraping.BaseScraper import BaseScraper

class LetterboxScraper(BaseScraper):

    def scrape(self):
        """
        Scrapes letterboxd.com for review pages.

        Works very similarly to the basic scrape function. Takes in ids
        from imdb and checks to see if they exist on letterboxd. If
        not, it will hit an exception and move on. Movies with no
        reviews also hit an exception. This is much slower than imbd
        due to differing website design.
        """
        id_list = self.get_ids()
        t = time.perf_counter()
        movie_id = []
        rating = []
        reviews = []
        username = []
        likes = []
        date = []
        review_id = []
        iteration_counter = 0
        broken = []
        page_count = 0

        query = """
        SELECT movie_id FROM movies
        """
        curs, conn = self.connect_to_database()
        curs.execute(query)
        movie_ids = set([row[0] for row in curs.fetchall()])

        for count, id in enumerate(id for id in id_list if id in movie_ids):
            print("----------------------------------------")
            try:
                t1 = time.perf_counter()

                review_count = 0

                # self.locate(id)

                url_initial = f"https://www.letterboxd.com/imdb/{id}"
                time.sleep(randint(3, 6))
                initial_response = requests.get(url_initial)
                title = ""
                try:
                    soup = BeautifulSoup(initial_response.text, 'html.parser')
                    title = soup.find(class_="headline-1 js-widont prettify").get_text()
                    title = title.replace(" ", "-").lower()

                except Exception as e:
                    print(f"Unable to find a title for this movie at index: \
{self.all_ids.index(id)}")
                    print("This is normal and expected behavior")
                    raise Exception(e)
                url_reviews = initial_response.url + 'reviews/by/activity/'
                print(url_reviews)
                # initially, I wanted to make this sorted by recency, but if
                # there are fewer than 12 reviews only sorting by popular is
                # available
                time.sleep(randint(3, 6))
                response = requests.get(url_reviews)
                if response.status_code != 200:
                        time.sleep(randint(3, 6))
                        response = requests.get(url_reviews)
                        if response.status_code != 200:
                            print(f"call to {url_reviews} failed with status \
code {response.status_code}!")
                            continue

                soup = BeautifulSoup(response.text, 'html.parser')
                items = soup.find_all(class_='film-detail')
                if len(items) == 0:
                    print(f"No reviews for {id} {title}")
                    continue
                print(f"ID: {id} at index {self.all_ids.index(id)}")
                while True:
                    if iteration_counter >= self.max_iter_count:
                        df = self.letterboxd_dataframe(movie_id, review_id,
                                                       rating, reviews, date,
                                                       username)
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
                            time.sleep(randint(3, 4))
                            fulltext = requests.get(text_url)
                            if fulltext.status_code != 200:
                                time.sleep(randint(3, 6))
                                fulltext = requests.get(text_url)
                                if fulltext.status_code != 200:
                                    print(f"call to {text_url} failed with \
status code {fulltext.status_code}!")
                                    continue
                            fulltext = re.sub(r'\<[^>]*\>', "", fulltext.text)
                            reviews.append(fulltext)

                        else:
                            reviews.append(body.get_text())
                        review_count += 1
                        movie_id.append(id.replace("tt", ""))
                        append = append.split(":", 1)[1].replace("/", "")
                        review_id.append(append)

                        try:
                            rating1 = str(item.find(class_="attribution"))
                            found = re.search(r'rating -green rated-\d+', rating1)
                            found = found.group()
                            text = found.split("-")
                            rate = int(text[-1])
                            rating.append(rate)
                        except Exception:
                            rating.append(11)
                        username.append(item.find(class_="name").get_text())

                        if item.find('span', '_nobr').get_text():
                            dates = item.find('span', '_nobr').get_text()
                            date.append(dates)
                        else:
                            datetime = str(item.find('time', class_="localtime-dd-mmm-yyyy"))
                            extract = datetime.split('"')
                            dates = str(extract[3])
                            date.append(dates[:10])

                    if soup.find('a', class_="next"):
                        page_count += 1
                        url_more = url_reviews + 'page/' + str(page_count+1) + '/'
                        print(url_more)
                        time.sleep(randint(3, 6))
                        response = requests.get(url_more)
                        if response.status_code != 200:
                            time.sleep(randint(3, 6))
                            response = requests.get(url_more)
                            if response.status_code != 200:
                                print(f"call to {url_more} failed with status \
code {response.status_code}!")
                                continue
                        soup = BeautifulSoup(response.text, 'html.parser')
                        items = soup.find_all(class_='film-detail')
                    else:
                        print('end of this movie')
                        page_count = 0
                        break
                    # While loop ends here

                t2 = time.perf_counter()
                finish = t2-t1

                # if count == 0 and os.path.exists(f"Logfile{self.scraper_instance}.txt"):
                #     os.remove(f"Logfile{self.scraper_instance}.txt")
                # print("Logging")
                # self.create_log(title,review_count,None,finish)

            except Exception as e:
                broken.append(id)
                print(sys.exc_info()[1])
                continue

        try:
            df = self.letterboxd_dataframe(movie_id, review_id, rating,
                                           reviews, date, username)
            self.letterboxd_insert(df)
        except Exception as e:
            print("error while creating dataframe or inserting into database")
            raise Exception(e)

        t3 = time.perf_counter()
        total = t3 - t
        print(f"Scraped {count + 1} movies in {round(total,2)} seconds")
        print('All done!\n')
        print("The following IDs were not scraped succcessfully:")
        self.show(broken)
        if len(broken) == 0:
            print("none")


    def letterboxd_dataframe(self, movie_id, review_id,
                             ratings, reviews, date, username):
        """
        Used in scrape_letterboxd to make and return a dataframe.
        """
        df = pd.DataFrame(
            {
                'movie_id': movie_id,
                'review_text': reviews,
                'user_rating': ratings,
                'username': username,
                'review_date': date,
                'review_id': review_id
                })
        df['review_date'] = pd.to_datetime(df['review_date'], errors='coerce')
        df['review_date'] = df['review_date'].fillna(method='ffill')
        df['review_date'] = df['review_date'].fillna(value='2012-12-21')
        df['review_date'] = df['review_date'].dt.strftime('%Y-%m-%d')
        print(df['review_date'])
        return df

    def letterboxd_insert(self, df):
        """
        Connects to the database and inserts reviews as new rows.

        Takes a dataframe and formats it into a very long string to
        convert to  SQL. Connects to the database, executes the query,
        and closes the cursor and connection.
        """
        # convert rows into tuples
        row_insertions = []
        for i in list(df.itertuples(index=False)):
            row_insertions.append((
                    i.movie_id,
                    i.review_date,
                    float(i.user_rating),
                    str(i.username),
                    str(i.review_text),
            ))
        row_insertions = row_insertions[:-2]
        cursor_boi, connection = self.connect_to_database()
        # create SQL INSERT query
        query = """
        INSERT INTO movie_reviews(movie_id, review_date, user_rating, user_name, review_text)
        VALUES (%s, %s, %s, %s, %s);
        """
        # execute query
        execute_batch(
            cursor_boi,
            query,
            row_insertions,
        )
        connection.commit()
        cursor_boi.close()
        connection.close()
        print("Insertion Complete")

