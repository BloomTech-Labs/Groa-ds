from scraper import * 
s = Scraper(start=15935, end=17705, max_iter=30, scraper_instance=125) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)