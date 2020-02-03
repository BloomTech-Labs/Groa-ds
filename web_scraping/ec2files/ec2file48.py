from scraper import * 
s = Scraper(start=85536, end=87317, max_iter=30, scraper_instance=48) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)