from scraper import * 
s = Scraper(start=181764, end=183545, max_iter=30, scraper_instance=102) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)