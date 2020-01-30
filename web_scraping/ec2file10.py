from scraper import * 
s = Scraper(start=24790, end=26560, max_iter=30, scraper_instance=130) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)