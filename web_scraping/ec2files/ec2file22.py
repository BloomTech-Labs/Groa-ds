from scraper import * 
s = Scraper(start=39204, end=40985, max_iter=30, scraper_instance=22) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)