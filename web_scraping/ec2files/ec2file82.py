from scraper import * 
s = Scraper(start=146124, end=147905, max_iter=30, scraper_instance=82) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)