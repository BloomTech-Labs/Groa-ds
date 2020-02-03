from scraper import * 
s = Scraper(start=256608, end=258389, max_iter=30, scraper_instance=144) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)