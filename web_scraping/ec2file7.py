from scraper import * 
s = Scraper(start=19477, end=21247, max_iter=30, scraper_instance=127) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)