from scraper import * 
s = Scraper(start=144342, end=146123, max_iter=30, scraper_instance=81) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)