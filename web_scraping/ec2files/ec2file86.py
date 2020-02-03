from scraper import * 
s = Scraper(start=153252, end=155033, max_iter=30, scraper_instance=86) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)