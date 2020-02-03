from scraper import * 
s = Scraper(start=32076, end=33857, max_iter=30, scraper_instance=18) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)