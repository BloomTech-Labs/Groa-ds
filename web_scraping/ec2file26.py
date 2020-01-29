from scraper import * 
s = Scraper(start=47816, end=49586, max_iter=500, scraper_instance=56) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)