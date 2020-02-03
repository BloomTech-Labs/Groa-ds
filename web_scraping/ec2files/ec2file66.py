from scraper import * 
s = Scraper(start=117612, end=119393, max_iter=30, scraper_instance=66) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)