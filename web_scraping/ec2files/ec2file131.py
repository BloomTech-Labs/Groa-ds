from scraper import * 
s = Scraper(start=233442, end=235223, max_iter=30, scraper_instance=131) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)