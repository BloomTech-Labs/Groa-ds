from scraper import * 
s = Scraper(start=224532, end=226313, max_iter=30, scraper_instance=126) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)