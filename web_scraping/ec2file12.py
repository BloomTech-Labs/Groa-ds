from scraper import * 
s = Scraper(start=26562, end=28332, max_iter=30, scraper_instance=102) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)