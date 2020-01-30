# Copy scrape_movies from ec2_launch to web_scraping, run this file,
# then delete the copy
scrape = open("scrape_movies.txt").read()
for i in range(30):
    f = open(f"scrape_movies{i}.txt", "a")
    f.write(f'{scrape}\nnohup python ec2file{i}.py &\necho "Scraping complete"\nexit')
