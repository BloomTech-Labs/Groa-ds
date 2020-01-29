from scraper import * 
s = Scraper(start=14167, end=15937, max_iter=500, scraper_instance=37) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)