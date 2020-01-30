from scraper import * 
s = Scraper(start=12393, end=14163, max_iter=30, scraper_instance=123) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)