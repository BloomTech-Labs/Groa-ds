from scraper import * 
s = Scraper(start=42501, end=44271, max_iter=30, scraper_instance=111) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)