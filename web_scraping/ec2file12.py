from scraper import * 
s = Scraper(start=28332, end=30102, max_iter=30, scraper_instance=132) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)