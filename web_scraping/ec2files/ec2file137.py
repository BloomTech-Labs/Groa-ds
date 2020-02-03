from scraper import * 
s = Scraper(start=244134, end=245915, max_iter=30, scraper_instance=137) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)