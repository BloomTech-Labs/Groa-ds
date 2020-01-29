from scraper import * 
s = Scraper(start=31877, end=33647, max_iter=30, scraper_instance=47) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)