from scraper import * 
s = Scraper(start=35640, end=37421, max_iter=30, scraper_instance=20) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)