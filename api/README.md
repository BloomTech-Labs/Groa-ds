# groa-ds-api

Recommender system for the Groa project. 

## local setup (with `pipenv`)

- navigate to `api/` directory
- run `pipenv install` to create `Pipefile.lock`
- run app using: `pipenv run python main.py`
- run tests using: `pipenv run pytest`

## local setup (with docker)

- navigate to `api/` directory
- run `docker build -t groadsapi .`
- run `docker run --env-file ./.env -p 8000:8000 --name groacontainer groadsapi`

## navigate to docs (includes route information)

Once this FastAPI is deployed will link prod docs here.

- run appy using `pipenv run python main.py` 
- navigate to `http://0.0.0.0:8000/docs` in browser