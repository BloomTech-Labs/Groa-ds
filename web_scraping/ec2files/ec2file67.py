from scraper import * 
s = Scraper(start=119394, end=121175, max_iter=30, scraper_instance=67) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)