from scraper import * 
s = Scraper(start=69498, end=71279, max_iter=30, scraper_instance=39) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)