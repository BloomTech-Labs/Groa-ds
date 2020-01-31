from scraper import * 
s = Scraper(start=14164, end=15934, max_iter=30, scraper_instance=124) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)