from scraper import * 
s = Scraper(start=10692, end=12473, max_iter=30, scraper_instance=6) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)