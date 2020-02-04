from scraper import * 
s = Scraper(start=17820, end=19601, max_iter=30, scraper_instance=10) 
s.scrape_letterboxd()