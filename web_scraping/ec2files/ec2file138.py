from scraper import * 
s = Scraper(start=245916, end=247697, max_iter=30, scraper_instance=138) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)