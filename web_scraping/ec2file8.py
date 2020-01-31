from scraper import * 
s = Scraper(start=19478, end=21248, max_iter=30, scraper_instance=98) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)