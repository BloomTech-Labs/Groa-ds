from scraper import * 
s = Scraper(start=197802, end=199583, max_iter=30, scraper_instance=111) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)