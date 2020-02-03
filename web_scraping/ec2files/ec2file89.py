from scraper import * 
s = Scraper(start=158598, end=160379, max_iter=30, scraper_instance=89) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)