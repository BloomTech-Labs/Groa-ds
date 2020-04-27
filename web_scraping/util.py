from web_scraping.ImdbScraper import ImdbScraper
from web_scraping.LetterboxScraper import LetterboxScraper


def run_scrapers(start, end):
    imdb = ImdbScraper(start, end, end-start)
    imdb.scrape()
    letterbox = LetterboxScraper(start, end, end-start)
    letterbox.scrape()

def run_scrapers_update(start, end):
    imdb = ImdbScraper(start, end, end-start)
    imdb.update()
    letterbox = LetterboxScraper(start, end, end-start)
    letterbox.scrape()
