from scraper import * 
s = Scraper(start=149688, end=151469, max_iter=30, scraper_instance=84) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)