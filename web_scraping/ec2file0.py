from scraper import * 
s = Scraper(start=7080, end=8850, max_iter=30, scraper_instance=120) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)