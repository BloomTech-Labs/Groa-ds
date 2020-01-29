from scraper import * 
s = Scraper(start=49587, end=51357, max_iter=30, scraper_instance=57) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)