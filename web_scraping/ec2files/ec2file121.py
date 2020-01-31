from scraper import * 
s = Scraper(start=215622, end=217403, max_iter=30, scraper_instance=121) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)