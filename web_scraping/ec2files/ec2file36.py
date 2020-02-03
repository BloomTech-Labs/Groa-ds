from scraper import * 
s = Scraper(start=64152, end=65933, max_iter=30, scraper_instance=36) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)