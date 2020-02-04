from scraper import * 
s = Scraper(start=89100, end=90881, max_iter=30, scraper_instance=50) 
s.scrape_letterboxd()