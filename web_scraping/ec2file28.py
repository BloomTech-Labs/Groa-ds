from scraper import * 
s = Scraper(start=54898, end=56668, max_iter=30, scraper_instance=118) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)