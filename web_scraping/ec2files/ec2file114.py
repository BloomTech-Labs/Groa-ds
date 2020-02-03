from scraper import * 
s = Scraper(start=203148, end=204929, max_iter=30, scraper_instance=114) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)