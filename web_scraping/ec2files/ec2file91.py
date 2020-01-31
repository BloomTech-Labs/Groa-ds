from scraper import * 
s = Scraper(start=162162, end=163943, max_iter=30, scraper_instance=91) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)