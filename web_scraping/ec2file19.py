from scraper import * 
s = Scraper(start=40729, end=42499, max_iter=30, scraper_instance=139) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)