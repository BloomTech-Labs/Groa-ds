from scraper import * 
s = Scraper(start=30104, end=31874, max_iter=30, scraper_instance=104) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)