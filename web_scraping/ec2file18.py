from scraper import * 
s = Scraper(start=31878, end=33648, max_iter=30, scraper_instance=18) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)