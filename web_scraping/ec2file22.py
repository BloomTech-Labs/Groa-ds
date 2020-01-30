from scraper import * 
s = Scraper(start=38962, end=40732, max_iter=30, scraper_instance=22) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)