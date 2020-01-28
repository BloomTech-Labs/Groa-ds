from decouple import config

number = int(config("NUMBER"))
start = number*1770
end = (number+1)*1770
instance = number*30



for i in range(30):
    f = open(f"ec2file{i}.py", "w")
    f.write(f"from scraper import * \ns = Scraper(start={start}, end={end}, max_iter=500, scraper_instance={instance}) \nids = s.get_ids() \ns.scrape_letterboxd(ids)")
    start = end + 1
    end = start + 1770
    instance += 1
    f.close()
