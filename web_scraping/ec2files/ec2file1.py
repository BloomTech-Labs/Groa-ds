from scraper import * 
s = Scraper(start=1782, end=3563, max_iter=30, scraper_instance=1) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)