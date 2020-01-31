from scraper import * 
s = Scraper(start=56668, end=58438, max_iter=30, scraper_instance=148) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)