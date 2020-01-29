from scraper import * 
s = Scraper(start=51358, end=53128, max_iter=500, scraper_instance=58) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)