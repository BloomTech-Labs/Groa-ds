from scraper import * 
s = Scraper(start=254826, end=256607, max_iter=30, scraper_instance=143) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)