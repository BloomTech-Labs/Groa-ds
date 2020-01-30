from scraper import * 
s = Scraper(start=23019, end=24789, max_iter=30, scraper_instance=129) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)