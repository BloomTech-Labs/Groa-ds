from scraper import * 
s = Scraper(start=58439, end=60209, max_iter=30, scraper_instance=149) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)