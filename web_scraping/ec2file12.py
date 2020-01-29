from scraper import * 
s = Scraper(start=23022, end=24792, max_iter=30, scraper_instance=42) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)