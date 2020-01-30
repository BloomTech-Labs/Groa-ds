from scraper import * 
s = Scraper(start=46042, end=47812, max_iter=30, scraper_instance=142) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)