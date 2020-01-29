from scraper import * 
s = Scraper(start=44274, end=46044, max_iter=500, scraper_instance=54) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)