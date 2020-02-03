from scraper import * 
s = Scraper(start=67716, end=69497, max_iter=30, scraper_instance=38) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)