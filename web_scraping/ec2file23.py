from scraper import * 
s = Scraper(start=47813, end=49583, max_iter=30, scraper_instance=143) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)