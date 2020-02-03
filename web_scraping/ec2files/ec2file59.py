from scraper import * 
s = Scraper(start=105138, end=106919, max_iter=30, scraper_instance=59) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)