from scraper import * 
s = Scraper(start=30103, end=31873, max_iter=30, scraper_instance=133) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)