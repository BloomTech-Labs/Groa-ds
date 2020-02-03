from scraper import * 
s = Scraper(start=265518, end=267299, max_iter=30, scraper_instance=149) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)