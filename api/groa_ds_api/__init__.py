from fastapi import FastAPI, BackgroundTasks
from groa_ds_api.utils import MovieUtility
from groa_ds_api.models import *
import os
from pathlib import Path
import redis
import pickle
from typing import List
from datetime import datetime


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

    @app.get("/", response_model=str)
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
        # can delete if you don't want new recs updating /explore results
        today = datetime.today().strftime('%Y-%m-%d')
        cache.delete("explore"+today)
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
        result = cache.get("sim"+payload.movie_id)
        if result is not None:
            result = pickle.loads(result)
            return result
        result = predictor.get_similar_movies(payload)
        cache.set("sim"+payload.movie_id, pickle.dumps(result))
        return result

    @app.get("/service-providers/{movie_id}", response_model=ProviderOutput)
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
        result = cache.get("prov"+movie_id)
        if result is not None:
            result = pickle.loads(result)
            return result
        result = predictor.get_service_providers(movie_id)
        cache.set("prov"+movie_id, pickle.dumps(result))
        return result
    
    @app.get("/explore", response_model=ExploreOutput)
    async def explore():
        """
        Sends a list of recent recommendations made by our API.

        Returns:
        - **data:** List[Movie]
        """
        today = datetime.today().strftime('%Y-%m-%d')
        result = cache.get("explore"+today)
        if result is not None:
            result = pickle.loads(result)
            return result
        result = predictor.get_recent_recommendations()
        cache.set("explore"+today, pickle.dumps(result))
        return result
    
    @app.get("/explore/{user_id}")
    async def explore_user(user_id: int):
        # the lists work to a degree but still need a title 
        result = cache.get("explore"+str(user_id))
        if result is not None:
            result = pickle.loads(result)
            return result
        result = predictor.get_recent_recommendations(user_id)
        cache.set("explore"+str(user_id), pickle.dumps(result))
        return result

    """ Start of Movie List routes """
    @app.post("/movie-list", response_model=MovieList)
    async def create_movie_list(payload: CreateListInput):
        """
        Given a `user_id` and `name`, we create a movie_list and return the 
        `list_id`.

        Parameters:
        - **user_id:** int
        - **name:** str

        Returns:
        - **list_id:** int
        """
        list_id = predictor.create_movie_list(payload)
        cache.delete("lists"+str(payload.user_id))
        if not payload.private:
            cache.delete("alllists")
        return list_id

    @app.get("/movie-list/all", response_model=List[MovieList])
    async def get_all_lists():
        result = cache.get("alllists")
        if result is not None:
            result = pickle.loads(result)
            return result
        result = predictor.get_all_lists()
        cache.set("alllists", pickle.dumps(result))
        return result

    @app.get("/movie-list/all/{user_id}", response_model=List[MovieList])
    async def get_user_lists(user_id: int):
        """
        Given a `user_id`, we grab a preview of all movie lists 
        the user has made.

        Parameters:
        - **user_id:** int

        Returns:
        - List[ListPreview]

        ListPreview Object:
        - list_id: int
        - name: str
        """
        result = cache.get("lists"+str(user_id))
        if result is not None:
            result = pickle.loads(result)
            return result
        result = predictor.get_user_lists(user_id)
        cache.set("lists"+str(user_id), pickle.dumps(result))
        return result

    @app.get("/movie-list/{list_id}", response_model=GetListOutput)
    async def get_movie_list(list_id: int):
        """
        Given a `list_id`, we grab that list and send back
        the list data.

        Parameters:
        - **list_id:** int

        Returns:
        - list_id: int
        - name: str
        - movie_list: List[Movie]
        - recs: List[Movie]
        """
        result = cache.get("movielist"+str(list_id))
        if result is not None:
            result = pickle.loads(result)
            return result
        result = predictor.get_movie_list(list_id)
        cache.set("movielist"+str(list_id), pickle.dumps(result))
        return result

    @app.put("/movie-list/{list_id}/add/{movie_id}", response_model=str)
    async def add_to_movie_list(list_id: int, movie_id: str):
        """
        Given a `list_id` and `movie_id`, we add that movie to the 
        list of the list_id provided.

        Parameters:
        - **list_id:** int
        - **movie_id:** str

        Returns:
        - result: str
        """
        result = predictor.add_to_movie_list(list_id, movie_id)
        cache.delete("movielist"+str(list_id))
        return result

    @app.put("/movie-list/{list_id}/remove/{movie_id}", response_model=str)
    async def remove_from_list(list_id: int, movie_id: str):
        """
        Given a `list_id` and `movie_id`, we remove the movie from the 
        list of the list_id provided.

        Parameters:
        - **list_id:** int
        - **movie_id:** str

        Returns:
        - result: str
        """
        result = predictor.remove_from_movie_list(list_id, movie_id)
        cache.delete("movielist"+str(list_id))
        return result

    @app.delete("/movie-list/{list_id}", response_model=str)
    async def delete_list(list_id: int):
        """
        Given a `list_id`, we delete that list.

        Parameters:
        - **list_id:** int

        Returns:
        - result: str
        """
        result = predictor.delete_movie_list(list_id)
        cache.delete("movielist"+str(list_id))
        cache.delete("lists"+str(result[0]))
        if result[1]:
            cache.delete("alllists")
        return "Success"
    """ End of Movie List routes """

    return app
