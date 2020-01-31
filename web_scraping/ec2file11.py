from scraper import * 
s = Scraper(start=26561, end=28331, max_iter=30, scraper_instance=131) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)