from scraper import * 
s = Scraper(start=114048, end=115829, max_iter=30, scraper_instance=64) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)