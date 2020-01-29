from scraper import * 
s = Scraper(start=53129, end=54899, max_iter=500, scraper_instance=59) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)