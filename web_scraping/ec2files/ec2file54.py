from scraper import * 
s = Scraper(start=96228, end=98009, max_iter=30, scraper_instance=54) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)