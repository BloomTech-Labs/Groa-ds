from scraper import * 
s = Scraper(start=263736, end=265517, max_iter=30, scraper_instance=148) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)