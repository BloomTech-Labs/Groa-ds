from scraper import * 
s = Scraper(start=44271, end=46041, max_iter=30, scraper_instance=141) 
ids = s.get_ids() 
s.scrape_letterboxd(ids)