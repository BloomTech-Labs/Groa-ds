from scraper import * 
s = Scraper(start=128304, end=130085, max_iter=30, scraper_instance=72) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)