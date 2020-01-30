from scraper import * 
s = Scraper(start=21252, end=23022, max_iter=30, scraper_instance=12) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)