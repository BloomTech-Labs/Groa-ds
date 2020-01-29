from scraper import * 
s = Scraper(start=33648, end=35418, max_iter=500, scraper_instance=48) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)