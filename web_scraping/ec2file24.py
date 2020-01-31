from scraper import * 
s = Scraper(start=47814, end=49584, max_iter=30, scraper_instance=114) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)