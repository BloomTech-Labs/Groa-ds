from scraper import * 
s = Scraper(start=71280, end=73061, max_iter=30, scraper_instance=40) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)