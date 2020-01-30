from scraper import * 
s = Scraper(start=37191, end=38961, max_iter=30, scraper_instance=21) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)