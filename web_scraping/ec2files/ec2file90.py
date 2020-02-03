from scraper import * 
s = Scraper(start=160380, end=162161, max_iter=30, scraper_instance=90) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)