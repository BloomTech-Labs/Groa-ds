from scraper import * 
s = Scraper(start=3541, end=5311, max_iter=500, scraper_instance=31) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)