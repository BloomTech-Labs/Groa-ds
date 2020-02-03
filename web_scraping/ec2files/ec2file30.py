from scraper import * 
s = Scraper(start=53460, end=55241, max_iter=30, scraper_instance=30) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)