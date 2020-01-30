from scraper import * 
s = Scraper(start=10622, end=12392, max_iter=30, scraper_instance=122) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)