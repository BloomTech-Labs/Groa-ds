from scraper import * 
s = Scraper(start=51678, end=53459, max_iter=30, scraper_instance=29) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)