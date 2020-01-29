from scraper import * 
s = Scraper(start=28335, end=30105, max_iter=30, scraper_instance=45) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)