from scraper import * 
s = Scraper(start=44275, end=46045, max_iter=30, scraper_instance=25) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)