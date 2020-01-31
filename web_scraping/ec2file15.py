from scraper import * 
s = Scraper(start=31875, end=33645, max_iter=30, scraper_instance=105) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)