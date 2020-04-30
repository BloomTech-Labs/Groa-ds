from fastapi import FastAPI, BackgroundTasks
from groa_ds_api.utils import MovieUtility
from fastapi import BackgroundTasks, FastAPI
from groa_ds_api.utils import Recommender
from groa_ds_api.models import RecInput, RecOutput, SimInput, SimOutput
import os
from pathlib import Path
import redis 
import pickle

app = FastAPI(
    title="groa-ds-api",
    description="Movie recommendations based on user ratings and preferences using a trained w2v model",
    version="1.0"
)

parent_path = Path(__file__).resolve().parents[1]
model_path = os.path.join(parent_path, 'w2v_limitingfactor_v3.51.model')

predictor = MovieUtility(model_path)

cache = redis.StrictRedis(host=os.getenv('REDIS_HOST'))


def create_app():

    @app.get("/")
    async def index():
        """
        Simple 'hello' from our API.
        """
        welcome_message = "This is the DS API for Groa"
        return welcome_message

    @app.post("/recommendations", response_model=RecOutput)
    async def get_recommendations(payload: RecInput, background_tasks: BackgroundTasks):
        """
        Given a `user_id`, the user's ratings are used to create a user's 'taste'
        vector. We then get the most similar movies to that vector using cosine similarity.

        Parameters:

        - **user_id:** int
        - num_recs: int [1, 100]
        - good_threshold: int [3, 5]
        - bad_threshold: int [1, 3]
        - harshness: int [1, 2]

        Returns:

        - **data:** List[Movie]

        `Will not always return as many recommendations as
        num_recs due to the algorithms filtering process.`
        """
        result = predictor.get_recommendations(payload, background_tasks)
        return result

    @app.post("/similar-movies", response_model=SimOutput)
    async def get_similar_movies(payload: SimInput):
        """
        Given a `movie_id`, we get the movie's vector using our trained `w2v` model.
        We then get the most similar movies to that vector using cosine similarity.

        Parameters:

        - **movie_id:** str
        - num_movies: int [1, 100]

        Returns:

        - **data:** List[Movie]

        `Will reliably return as many recommendations as indicated
        in num_movies parameter.`
        """
        result = cache.get(payload.movie_id)
        if result is not None:
            result = pickle.loads(result)
            return result
        result = predictor.get_similar_movies(payload)
        cache.set(payload.movie_id, pickle.dumps(result))
        return result
    
    @app.get("/service-providers/{movie_id}")
    async def service_providers(movie_id: str):
        """
        Given a `movie_id`, we provide the service providers and the links 
        to the movie of that service provider for quick access to the film.

        Parameters:
        - **movie_id:** str

        Returns:
        - **data:** List[Provider]

        Provider Object:
        - provider_id
        - name
        - link
        - presentation_type (HD or SD)
        - monetization_type (buy, rent or flatrate)
        """
        result = cache.get(movie_id)
        if result is not None:
            result = pickle.loads(result)
            return result
        result = predictor.get_service_providers(movie_id)
        cache.set(movie_id, pickle.dumps(result))
        return result

    return app
