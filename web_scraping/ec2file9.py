from scraper import * 
s = Scraper(start=15939, end=17709, max_iter=30, scraper_instance=9) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)