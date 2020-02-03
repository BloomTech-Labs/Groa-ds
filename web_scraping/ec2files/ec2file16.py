from scraper import * 
s = Scraper(start=28512, end=30293, max_iter=30, scraper_instance=16) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)