from scraper import * 
s = Scraper(start=208494, end=210275, max_iter=30, scraper_instance=117) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)