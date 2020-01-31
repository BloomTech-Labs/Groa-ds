from scraper import * 
s = Scraper(start=12394, end=14164, max_iter=30, scraper_instance=94) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)