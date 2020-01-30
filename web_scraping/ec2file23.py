from scraper import * 
s = Scraper(start=40733, end=42503, max_iter=30, scraper_instance=23) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)