from scraper import * 
s = Scraper(start=17709, end=19479, max_iter=500, scraper_instance=39) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)