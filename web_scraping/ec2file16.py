from scraper import * 
s = Scraper(start=28336, end=30106, max_iter=30, scraper_instance=16) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)