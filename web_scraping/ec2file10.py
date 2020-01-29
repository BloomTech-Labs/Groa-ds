from scraper import * 
s = Scraper(start=19480, end=21250, max_iter=30, scraper_instance=40) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)