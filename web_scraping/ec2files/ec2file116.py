from scraper import * 
s = Scraper(start=206712, end=208493, max_iter=30, scraper_instance=116) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)