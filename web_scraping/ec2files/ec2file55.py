from scraper import * 
s = Scraper(start=98010, end=99791, max_iter=30, scraper_instance=55) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)