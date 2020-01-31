from scraper import * 
s = Scraper(start=237006, end=238787, max_iter=30, scraper_instance=133) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)