from scraper import * 
s = Scraper(start=35416, end=37186, max_iter=30, scraper_instance=136) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)