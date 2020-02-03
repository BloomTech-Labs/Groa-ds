from scraper import *
s = Scraper(start=267300, end=267421, max_iter=30, scraper_instance=150) 
ids = s.get_ids()
s.scrape_letterboxd(ids)
