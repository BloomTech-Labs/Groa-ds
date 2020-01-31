from scraper import * 
s = Scraper(start=14165, end=15935, max_iter=30, scraper_instance=95) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)