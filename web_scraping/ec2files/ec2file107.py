from scraper import * 
s = Scraper(start=190674, end=192455, max_iter=30, scraper_instance=107) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)