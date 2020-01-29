from scraper import * 
s = Scraper(start=8854, end=10624, max_iter=30, scraper_instance=34) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)