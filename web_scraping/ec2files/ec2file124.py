from scraper import * 
s = Scraper(start=220968, end=222749, max_iter=30, scraper_instance=124) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)