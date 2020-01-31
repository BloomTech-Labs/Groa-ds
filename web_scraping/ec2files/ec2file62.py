from scraper import * 
s = Scraper(start=110484, end=112265, max_iter=30, scraper_instance=62) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)