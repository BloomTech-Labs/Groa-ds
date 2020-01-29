from scraper import * 
s = Scraper(start=35419, end=37189, max_iter=30, scraper_instance=49) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)