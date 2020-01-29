from scraper import * 
s = Scraper(start=30106, end=31876, max_iter=500, scraper_instance=46) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)