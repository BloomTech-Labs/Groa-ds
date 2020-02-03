from scraper import * 
s = Scraper(start=78408, end=80189, max_iter=30, scraper_instance=44) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)