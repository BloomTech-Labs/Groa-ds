from scraper import * 
s = Scraper(start=19481, end=21251, max_iter=30, scraper_instance=11) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)