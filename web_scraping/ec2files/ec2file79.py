from scraper import * 
s = Scraper(start=140778, end=142559, max_iter=30, scraper_instance=79) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)