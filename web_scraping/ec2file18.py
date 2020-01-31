from scraper import * 
s = Scraper(start=37188, end=38958, max_iter=30, scraper_instance=108) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)