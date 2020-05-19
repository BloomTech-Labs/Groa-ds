# groa-ds-api

#### [live API](https://ds.groa.us) | [live API docs](https://ds.groa.us/docs)

Recommender system for the Groa project. 

## local setup (with docker-compose)

- navigate to `api/` directory
- run `docker-compose build`
- run `docker-compose up`
- API will be running on `http://localhost:5000`

## local setup (with pipenv)

- navigate to `api/` directory
- run `pipenv install`
- set REDIS_HOST in `.env` to "localhost"
- run redis server locally with `redis-server` (will have to install with homebrew prior)
- then: 
    - run app with `pipenv run python main.py`
    - test app with `pipenv run pytest`

## enviroment variables needed

- DB_USER
- DB_PASSWORD
- HOST
- PORT
- DB_NAME
- REDIS_HOST
- ELASTIC
- ACCESS_ID
- ACCESS_SECRET

## deployment instructions

- build image `docker build . -t groadsapi`
- tag image for dockerhub `docker tag groadsapi account/groa-ds-api:tagname`
- push image to dockerhub `docker push account/groa-ds-api:tagname`
- adjust image in `Dockerrun.aws.json`
- *optional* test deploy to staging `eb create staging` -> delete once complete
- deploy to production `eb deploy prod`