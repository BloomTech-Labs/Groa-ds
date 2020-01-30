from scraper import * 
s = Scraper(start=1771, end=3541, max_iter=30, scraper_instance=1) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)