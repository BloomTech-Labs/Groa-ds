from scraper import * 
s = Scraper(start=24791, end=26561, max_iter=30, scraper_instance=101) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)