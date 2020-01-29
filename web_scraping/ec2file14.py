from scraper import * 
s = Scraper(start=26564, end=28334, max_iter=500, scraper_instance=44) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)