from scraper import * 
s = Scraper(start=12396, end=14166, max_iter=500, scraper_instance=36) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)