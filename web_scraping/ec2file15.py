from scraper import * 
s = Scraper(start=33645, end=35415, max_iter=30, scraper_instance=135) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)