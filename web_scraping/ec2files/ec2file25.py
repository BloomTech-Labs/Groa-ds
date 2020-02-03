from scraper import * 
s = Scraper(start=44550, end=46331, max_iter=30, scraper_instance=25) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)