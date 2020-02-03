from scraper import * 
s = Scraper(start=247698, end=249479, max_iter=30, scraper_instance=139) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)