from scraper import * 
s = Scraper(start=8851, end=10621, max_iter=30, scraper_instance=121) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)