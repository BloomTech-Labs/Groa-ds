from scraper import * 
s = Scraper(start=8852, end=10622, max_iter=30, scraper_instance=92) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)