from scraper import * 
s = Scraper(start=30294, end=32075, max_iter=30, scraper_instance=17) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)