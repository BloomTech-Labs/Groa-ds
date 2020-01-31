from scraper import * 
s = Scraper(start=40730, end=42500, max_iter=30, scraper_instance=110) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)