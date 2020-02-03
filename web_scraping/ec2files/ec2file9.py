from scraper import * 
s = Scraper(start=16038, end=17819, max_iter=30, scraper_instance=9) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)