from scraper import * 
s = Scraper(start=55242, end=57023, max_iter=30, scraper_instance=31) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)