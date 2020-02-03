from scraper import * 
s = Scraper(start=194238, end=196019, max_iter=30, scraper_instance=109) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)