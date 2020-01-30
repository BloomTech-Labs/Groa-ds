from scraper import * 
s = Scraper(start=7084, end=8854, max_iter=30, scraper_instance=4) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)