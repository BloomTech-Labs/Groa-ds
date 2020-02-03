from scraper import * 
s = Scraper(start=226314, end=228095, max_iter=30, scraper_instance=127) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)