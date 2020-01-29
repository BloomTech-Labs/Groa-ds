from scraper import * 
s = Scraper(start=24793, end=26563, max_iter=500, scraper_instance=43) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)