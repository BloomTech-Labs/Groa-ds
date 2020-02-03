from scraper import * 
s = Scraper(start=179982, end=181763, max_iter=30, scraper_instance=101) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)