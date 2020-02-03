from scraper import * 
s = Scraper(start=238788, end=240569, max_iter=30, scraper_instance=134) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)