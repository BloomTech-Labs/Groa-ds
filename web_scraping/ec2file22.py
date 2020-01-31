from scraper import * 
s = Scraper(start=44272, end=46042, max_iter=30, scraper_instance=112) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)