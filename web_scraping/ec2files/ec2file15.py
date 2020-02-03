from scraper import * 
s = Scraper(start=26730, end=28511, max_iter=30, scraper_instance=15) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)