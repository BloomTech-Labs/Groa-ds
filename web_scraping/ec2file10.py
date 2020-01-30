from scraper import * 
s = Scraper(start=17710, end=19480, max_iter=30, scraper_instance=10) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)