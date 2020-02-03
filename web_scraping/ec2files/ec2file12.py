from scraper import * 
s = Scraper(start=21384, end=23165, max_iter=30, scraper_instance=12) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)