from scraper import * 
s = Scraper(start=37187, end=38957, max_iter=30, scraper_instance=137) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)