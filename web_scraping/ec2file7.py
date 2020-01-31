from scraper import * 
s = Scraper(start=17707, end=19477, max_iter=30, scraper_instance=97) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)