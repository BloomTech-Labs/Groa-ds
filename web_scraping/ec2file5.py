from scraper import * 
s = Scraper(start=10625, end=12395, max_iter=30, scraper_instance=35) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)