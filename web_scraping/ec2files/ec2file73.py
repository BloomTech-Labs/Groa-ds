from scraper import * 
s = Scraper(start=130086, end=131867, max_iter=30, scraper_instance=73) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)