from scraper import * 
s = Scraper(start=7083, end=8853, max_iter=500, scraper_instance=33) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)