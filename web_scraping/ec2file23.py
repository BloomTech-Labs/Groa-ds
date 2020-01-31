from scraper import * 
s = Scraper(start=46043, end=47813, max_iter=30, scraper_instance=113) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)