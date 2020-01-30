from scraper import * 
s = Scraper(start=53126, end=54896, max_iter=30, scraper_instance=146) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)