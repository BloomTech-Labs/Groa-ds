from ImdbScraper import ImdbScraper
from LetterboxScraper import LetterboxScraper

step = 100
def run_scrapers(start, end):
    scraper = ImdbScraper(start, end, step)
    num_max_ids = len(scraper.get_ids())
    for ix in range(start, start+num_max_ids, step):
        letterbox = LetterboxScraper(ix, ix+step, step)
        letterbox.scrape()
        imdb = ImdbScraper(ix, ix+step, step)
        imdb.scrape()

def run_scrapers_update(start, end):
    scraper = ImdbScraper(start, end, step)
    num_max_ids = len(scraper.get_ids())
    for ix in range(start, end, step):
        imdb = ImdbScraper(ix, ix+step, step)
        imdb.update()
        letterbox = LetterboxScraper(ix, ix+step, step)
        letterbox.scrape()
