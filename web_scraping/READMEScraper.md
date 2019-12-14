# Web Scraping

General overview of our process, why we made certain choices, and what data is ultimately being fed into our DB.


## Quick Rundown of the Scraper

As of (12/13/19) this scraper uses a list of movie IDs which were pulled from the tarbal files published by IMDb to return movie reviews and ratings.

In addition to reviews and ratings, the scraper pulls some information which will not be implemented in the initial skeleton model, but which may be used in the future model iterations.
(Date of review, How many people found review helpful, etc.)

### Blockers

12/13/19 - We hit a snag which prevents us from populating the RDS DB tables with data output from the scraper. We believe it is isolated to a misconfiguration of


### Installing

In order to run you will need to setup an AWS RDS DB

Start of walkthrough for launching EC2:
(Download the keypair
cd into the folder you have the keypair stored
connect using the example provided by AWS
type yes and press enter when prompted )

#### Configure EC2 to run scraper

Switch into root so we don't have to sudo call everything
```
sudo su
```

Update the yum package
```
yum update -y
```

Installing git
```
yum install git -y
```

Installing pip
```
yum -y install python-pip
```

Check to see you have the correct version
```
python -V
```

Installing python to the ec2 instance
```
yum install python3 python3-pip -y
```

Remove old version of python
```
sudo rm /usr/bin/python
```

Move the version of python you just downloaded into the default path
```
sudo ln -s /usr/bin/python3.7 /usr/bin/python
```

Check to see you have the correct version
```
python -V
```

Clone the repo which holds the scraper
```
git clone [repoclonelink]
```

CD into the repo
```
cd movie-recommender
```

CD into the scraper folder

```
cd web_scraping
```

Installing pipenv
```
pip install pipenv
```

Installing pipenv with the current version of python
```
pipenv install --python /usr/bin/python
```

Launch the shell and enter
```
pipenv shell
```

Sync the shell to install dependencies
```
pipenv sync
```

The psycopg2 install always fails but you can install the binary pkg and it works
```
pip3 install psycopg2-binary
```

## Deployment

Run:
```
python scraper[].py
```

## Built With

* [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/) - Python Library for pulling HTML data
* [psycopg2](https://pypi.org/project/psycopg2/) - PostgresSQL database adapter
* [Amazon RDS](https://aws.amazon.com/rds/?nc2=h_ql_prod_fs_rds) - The scraper outputs into two RDS DB tables
