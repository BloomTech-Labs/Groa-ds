from scraper import * 
s = Scraper(start=137214, end=138995, max_iter=30, scraper_instance=77) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)