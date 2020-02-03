from scraper import * 
s = Scraper(start=74844, end=76625, max_iter=30, scraper_instance=42) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)