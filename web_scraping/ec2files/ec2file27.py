from scraper import * 
s = Scraper(start=48114, end=49895, max_iter=30, scraper_instance=27) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)