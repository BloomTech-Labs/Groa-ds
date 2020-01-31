from scraper import * 
s = Scraper(start=192456, end=194237, max_iter=30, scraper_instance=108) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)