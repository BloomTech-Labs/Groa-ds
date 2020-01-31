from scraper import * 
s = Scraper(start=38959, end=40729, max_iter=30, scraper_instance=109) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)