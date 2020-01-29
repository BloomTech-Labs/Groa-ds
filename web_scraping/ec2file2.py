from scraper import * 
s = Scraper(start=5312, end=7082, max_iter=500, scraper_instance=32) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)