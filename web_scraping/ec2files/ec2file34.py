from scraper import * 
s = Scraper(start=60588, end=62369, max_iter=30, scraper_instance=34) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)