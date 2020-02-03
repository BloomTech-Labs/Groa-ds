from scraper import * 
s = Scraper(start=240570, end=242351, max_iter=30, scraper_instance=135) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)