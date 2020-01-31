from scraper import * 
s = Scraper(start=54897, end=56667, max_iter=30, scraper_instance=147) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)