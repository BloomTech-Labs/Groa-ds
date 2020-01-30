from scraper import * 
s = Scraper(start=12397, end=14167, max_iter=30, scraper_instance=7) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)