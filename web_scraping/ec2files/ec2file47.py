from scraper import * 
s = Scraper(start=83754, end=85535, max_iter=30, scraper_instance=47) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)