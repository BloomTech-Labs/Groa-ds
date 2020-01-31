from scraper import * 
s = Scraper(start=51356, end=53126, max_iter=30, scraper_instance=116) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)