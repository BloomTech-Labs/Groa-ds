from web_scraping.ImdbScraper import ImdbScraper
from web_scraping.LetterboxScraper import LetterboxScraper


def run_scrapers(start, end):
    imdb = ImdbScraper(start, end, 2**31)
    imdb.update()
    letterbox = LetterboxScraper(start, end, 2**31)
    letterbox.scrape()
