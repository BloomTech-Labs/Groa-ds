from scraper import * 
s = Scraper(start=133650, end=135431, max_iter=30, scraper_instance=75) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)