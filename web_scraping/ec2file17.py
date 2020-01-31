from scraper import * 
s = Scraper(start=35417, end=37187, max_iter=30, scraper_instance=107) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)