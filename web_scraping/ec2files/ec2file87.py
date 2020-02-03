from scraper import * 
s = Scraper(start=155034, end=156815, max_iter=30, scraper_instance=87) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)