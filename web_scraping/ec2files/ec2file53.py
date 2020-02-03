from scraper import * 
s = Scraper(start=94446, end=96227, max_iter=30, scraper_instance=53) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)