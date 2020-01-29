from scraper import * 
s = Scraper(start=40732, end=42502, max_iter=500, scraper_instance=52) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)