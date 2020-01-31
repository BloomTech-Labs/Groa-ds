from scraper import * 
s = Scraper(start=49585, end=51355, max_iter=30, scraper_instance=115) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)