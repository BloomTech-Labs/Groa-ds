from scraper import * 
s = Scraper(start=219186, end=220967, max_iter=30, scraper_instance=123) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)