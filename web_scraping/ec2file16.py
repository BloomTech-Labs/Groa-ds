from scraper import * 
s = Scraper(start=33646, end=35416, max_iter=30, scraper_instance=106) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)