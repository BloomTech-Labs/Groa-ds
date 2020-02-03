from scraper import * 
s = Scraper(start=204930, end=206711, max_iter=30, scraper_instance=115) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)