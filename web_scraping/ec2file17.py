from scraper import * 
s = Scraper(start=30107, end=31877, max_iter=30, scraper_instance=17) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)