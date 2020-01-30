from scraper import * 
s = Scraper(start=49588, end=51358, max_iter=30, scraper_instance=28) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)