from scraper import * 
s = Scraper(start=49584, end=51354, max_iter=30, scraper_instance=144) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)