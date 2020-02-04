start = 0
end = 1781
instance = 0


for i in range(150):
    f = open(f"ec2files/ec2file{i}.py", "w")
    f.write(f"from scraper import * \ns = Scraper(start={start}, end={end}, max_iter=30, scraper_instance={instance}) \ns.scrape_letterboxd()")
    start = end + 1
    end = start + 1781
    instance += 1
    f.close()
