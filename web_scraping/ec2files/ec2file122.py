from scraper import * 
s = Scraper(start=217404, end=219185, max_iter=30, scraper_instance=122) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)