from scraper import * 
s = Scraper(start=21249, end=23019, max_iter=30, scraper_instance=99) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)