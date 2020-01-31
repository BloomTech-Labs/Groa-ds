from scraper import * 
s = Scraper(start=90882, end=92663, max_iter=30, scraper_instance=51) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)