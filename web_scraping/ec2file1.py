from scraper import * 
s = Scraper(start=7081, end=8851, max_iter=30, scraper_instance=91) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)