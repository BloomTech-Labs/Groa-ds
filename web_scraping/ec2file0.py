from scraper import * 
s = Scraper(start=5310, end=7080, max_iter=30, scraper_instance=90) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)