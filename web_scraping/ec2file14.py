from scraper import * 
s = Scraper(start=31874, end=33644, max_iter=30, scraper_instance=134) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)