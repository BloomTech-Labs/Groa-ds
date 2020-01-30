from scraper import * 
s = Scraper(start=38958, end=40728, max_iter=30, scraper_instance=138) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)