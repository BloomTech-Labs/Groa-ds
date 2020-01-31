from scraper import * 
s = Scraper(start=126522, end=128303, max_iter=30, scraper_instance=71) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)