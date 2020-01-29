from scraper import * 
s = Scraper(start=15938, end=17708, max_iter=30, scraper_instance=38) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)