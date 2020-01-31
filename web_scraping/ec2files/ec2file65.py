from scraper import * 
s = Scraper(start=115830, end=117611, max_iter=30, scraper_instance=65) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)