from scraper import * 
s = Scraper(start=42500, end=44270, max_iter=30, scraper_instance=140) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)