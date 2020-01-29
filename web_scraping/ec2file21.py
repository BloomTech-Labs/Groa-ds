from scraper import * 
s = Scraper(start=38961, end=40731, max_iter=30, scraper_instance=51) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)