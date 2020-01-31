from scraper import * 
s = Scraper(start=213840, end=215621, max_iter=30, scraper_instance=120) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)