from scraper import * 
s = Scraper(start=242352, end=244133, max_iter=30, scraper_instance=136) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)