# groa-ds-api

#### [live API](https://ds.groa.us) | [live API docs](https://ds.groa.us/docs)

Recommender system for the Groa project. 

## local setup (with docker-compose)

- navigate to `api/` directory
- run `docker-compose build`
- run `docker-compose up`
- API will be running on `http://localhost:5000`

## enviroment variables needed

- DB_USER
- DB_PASSWORD
- HOST
- PORT
- DB_NAME
- REDIS_HOST