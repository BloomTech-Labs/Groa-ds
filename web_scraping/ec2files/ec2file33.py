from scraper import * 
s = Scraper(start=58806, end=60587, max_iter=30, scraper_instance=33) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)