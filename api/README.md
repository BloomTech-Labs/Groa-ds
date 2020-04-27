# groa-ds-api

#### [live API](https://ds.groa.us) | [live API docs](https://ds.groa.us/docs)

Recommender system for the Groa project. 

## local setup (with `pipenv`)

- navigate to `api/` directory
- run `pipenv install` to create `Pipefile.lock`
- run app using: `pipenv run python main.py`
- run tests using: `pipenv run pytest`

## local setup (with docker)

- navigate to `api/` directory
- run `docker build -t groadsapi .`
- run `docker run --env-file ./.env -p 5000:5000 --name groacontainer groadsapi`

## navigate to local docs (includes route information)

- run appy using `pipenv run python main.py` 
- navigate to `http://0.0.0.0:5000/docs` in browser