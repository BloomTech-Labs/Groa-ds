from scraper import * 
s = Scraper(start=15936, end=17706, max_iter=30, scraper_instance=96) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)