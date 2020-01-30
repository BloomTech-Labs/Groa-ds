from scraper import * 
s = Scraper(start=17706, end=19476, max_iter=30, scraper_instance=126) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)