from scraper import * 
s = Scraper(start=51355, end=53125, max_iter=30, scraper_instance=145) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)