from scraper import * 
s = Scraper(start=171072, end=172853, max_iter=30, scraper_instance=96) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)