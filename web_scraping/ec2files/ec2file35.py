from scraper import * 
s = Scraper(start=62370, end=64151, max_iter=30, scraper_instance=35) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)