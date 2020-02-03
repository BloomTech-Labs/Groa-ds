from scraper import * 
s = Scraper(start=142560, end=144341, max_iter=30, scraper_instance=80) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)