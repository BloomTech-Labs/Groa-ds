from scraper import * 
s = Scraper(start=42503, end=44273, max_iter=500, scraper_instance=53) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)