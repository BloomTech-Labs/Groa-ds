from scraper import * 
s = Scraper(start=163944, end=165725, max_iter=30, scraper_instance=92) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)