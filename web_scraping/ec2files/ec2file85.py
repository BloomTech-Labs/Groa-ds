from scraper import * 
s = Scraper(start=151470, end=153251, max_iter=30, scraper_instance=85) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)