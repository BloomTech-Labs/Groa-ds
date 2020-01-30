from scraper import * 
s = Scraper(start=14168, end=15938, max_iter=30, scraper_instance=8) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)