from scraper import * 
s = Scraper(start=131868, end=133649, max_iter=30, scraper_instance=74) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)