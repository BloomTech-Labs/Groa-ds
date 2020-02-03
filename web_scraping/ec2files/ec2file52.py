from scraper import * 
s = Scraper(start=92664, end=94445, max_iter=30, scraper_instance=52) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)