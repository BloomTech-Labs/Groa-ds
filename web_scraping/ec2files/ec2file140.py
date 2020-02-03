from scraper import * 
s = Scraper(start=249480, end=251261, max_iter=30, scraper_instance=140) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)