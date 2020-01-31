from scraper import * 
s = Scraper(start=23020, end=24790, max_iter=30, scraper_instance=100) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)