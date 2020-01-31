from scraper import * 
s = Scraper(start=21248, end=23018, max_iter=30, scraper_instance=128) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)