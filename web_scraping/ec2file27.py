from scraper import * 
s = Scraper(start=47817, end=49587, max_iter=30, scraper_instance=27) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)