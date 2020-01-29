from scraper import * 
s = Scraper(start=1770, end=3540, max_iter=30, scraper_instance=30) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)