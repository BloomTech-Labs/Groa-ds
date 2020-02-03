from scraper import * 
s = Scraper(start=106920, end=108701, max_iter=30, scraper_instance=60) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)