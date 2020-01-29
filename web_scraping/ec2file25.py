from scraper import * 
s = Scraper(start=46045, end=47815, max_iter=30, scraper_instance=55) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)