from scraper import * 
s = Scraper(start=8910, end=10691, max_iter=30, scraper_instance=5) 
s.scrape_letterboxd()