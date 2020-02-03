from scraper import * 
s = Scraper(start=46332, end=48113, max_iter=30, scraper_instance=26) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)