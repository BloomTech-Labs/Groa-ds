from scraper import * 
s = Scraper(start=121176, end=122957, max_iter=30, scraper_instance=68) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)