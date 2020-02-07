# Review2Vec model guide


This script does the following:
- Serializes tokenized IMDb user review histories
- Trains Doc2Vec on those histories
- Finds similar reviewers by writing style for a test set of reviews.

It can be run locally, but we cloned to an EC2 instance due to the fact that it can take days to download and prepare all the training data. Here are the instructions for using the R2V_trainer to train Doc2Vec on movie reviews.

1. Ensure you have a database with scraped movie reviews and movie data. See the Groa/web_scraping folder for a [scraper](https://github.com/Lambda-School-Labs/Groa/blob/master/web_scraping/scraper.py) you can use to get the reviews. Movie data can be found [here](https://datasets.imdbws.com/). You'll want the files 'title.basics.tsv.gz' and 'title.ratings.tsv.gz'. Make sure that you update the credentials in R2V_trainer to match your database.

2. Ensure that pipenv is installed with `pip install pipenv`.

2. In your terminal, run:
```
cd Groa/review2vec
pipenv install
pipenv shell
python R2V_trainer.py
```
3. You will be prompted for the database password if getpass() is used in the password credentials. Enter your password.
4. A set of options will appear. If you're running the script for the first time, you can simply run the commands in sequence.
5. Alternatively, you can use the bash script to run the trainer in the background. This will save the data as it prepares it (there is a lot of it) and train the models after all the data is prepared. To do this, run in your BASH terminal:
```
cd Groa/review2vec
pipenv install
pipenv shell
nohup bash command.sh &
```
