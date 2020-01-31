from scraper import * 
s = Scraper(start=56669, end=58439, max_iter=30, scraper_instance=119) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)