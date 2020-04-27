import pandas as pd
import requests
from bs4 import BeautifulSoup

from BaseScraper import BaseScraper

class FinderScraper(BaseScraper):

    def scrape(self):
        """
        Grabs all the names and urls of all the movies on Netflix.
        Finder.com has all the movies on Netflix on a single page.
        Scrapes them and adds them to the database.
        """
        url = f'https://www.finder.com/netflix-movies'
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        items = soup.find_all(class_='btn-success')
        links = [item['href'] for item in items]
        rows = soup.find_all(scope="row")
        titles = []
        for row in rows:
            if row['data-title'] == 'title':
                titles.append(row.get_text())
        df = pd.DataFrame({'title': titles, 'url': links})
        row_insertions = ""
        for i in list(df.itertuples(index=False)):
            row_insertions += str((i.title, i.url)) + ", "
        row_insertions = row_insertions[:-2]
        cursor_boi, connection = self.connect_to_database()
        query = "INSERT INTO netflix_urls(title, url) VALUES " + row_insertions + ";"
        cursor_boi.execute(query)
        connection.commit()
        cursor_boi.close()
        connection.close()
        print("Insertion Complete")
