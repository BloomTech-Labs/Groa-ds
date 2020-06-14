from fastapi import FastAPI, BackgroundTasks, HTTPException
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

        - **user_id:** str
        - num_recs: int [1, 100]
        - good_threshold: int [3, 5]
        - bad_threshold: int [1, 3]
        - harshness: int [1, 2]

        Returns:

        - **data:** List[Movie]

        `Will not always return as many recommendations as 
        num_recs due to the algorithms filtering process.`
        """
        result = cache.get("recs"+payload.user_id)
        if result is not None:
            result = pickle.loads(result)
            return result
        result = predictor.get_recommendations(payload, background_tasks)
        cache.set("recs"+payload.user_id, pickle.dumps(result))
        return result

    @app.get("/recommendations/interaction/{user_id}/{movie_id}", response_model=str)
    async def interact_with_rec(user_id: str, movie_id: str):
        """
        Given a `user_id` and `movie_id`, we update the movie recommendation to have
        an interaction value of `TRUE`.

        Parameters:

        - **rec_id:** str
        - **movie_id:** str
        """
        result = predictor.add_interaction(user_id, movie_id)
        if result == "Failure":
            raise HTTPException(status_code=404, detail="Invalid request.")
        return result

    @app.post("/rating", response_model=str)
    async def add_rating(payload: RatingInput):
        """
        Given the `RatingInput`, we add the rating to the DB and 
        remove cached recs to account for new info collected.

        Parameters:

        - **user_id:** str
        - **movie_id:** str
        - **rating:** float
        """
        result = predictor.add_rating(payload)
        if result == "Failure":
            raise HTTPException(status_code=404, detail="Invalid request.")
        cache.delete("recs"+payload.user_id)
        return result

    @app.post("/rating/{user_id}/remove/{movie_id}", response_model=str)
    async def remove_rating(user_id: str, movie_id: str):
        """
        Given the user_id and movie_id, we remove a user's rating
        from the users_rating table in the DB.

        Parameters:
        - **user_id** str
        - **movie_id** str
        """
        result = predictor.remove_rating(user_id, movie_id)
        if result == "Failure":
            raise HTTPException(status_code=404, detail="Invalid request.")
        cache.delete("recs"+user_id)
        return result

    @app.post("/watchlist", response_model=str)
    async def add_to_watchlist(payload: UserAndMovieInput):
        """
        Given the `UserAndMovieInput`, the movie is added to the
        user's watchlist.
        """
        result = predictor.add_to_watchlist(payload)
        if result == "Failure":
            raise HTTPException(status_code=404, detail="Invalid request.")
        cache.delete("recs"+payload.user_id)
        return result

    @app.post("/watchlist/{user_id}/remove/{movie_id}", response_model=str)
    async def remove_watchlist(user_id: str, movie_id: str):
        """
        Given the user_id and movie_id, we remove a user's watchlist
        from the users_watchlist table in the DB.

        Parameters:
        - **user_id** str
        - **movie_id** str
        """
        result = predictor.remove_watchlist(user_id, movie_id)
        if result == "Failure":
            raise HTTPException(status_code=404, detail="Invalid request.")
        cache.delete("recs"+user_id)
        return result

    @app.post("/notwatchlist", response_model=str)
    async def add_to_notwatchlist(payload: UserAndMovieInput):
        """
        Given the `UserAndMovieInput`, the movie is added to the
        user's willnotwatchlist.
        """
        result = predictor.add_to_notwatchlist(payload)
        if result == "Failure":
            raise HTTPException(status_code=404, detail="Invalid request.")
        cache.delete("recs"+payload.user_id)
        return result

    @app.post("/notwatchlist/{user_id}/remove/{movie_id}", response_model=str)
    async def remove_notwatchlist(user_id: str, movie_id: str):
        """
        Given the user_id and movie_id, we remove a user's notwatchlist
        from the users_notwatchlist table in the DB.

        Parameters:
        - **user_id** str
        - **movie_id** str
        """
        result = predictor.remove_notwatchlist(user_id, movie_id)
        if result == "Failure":
            raise HTTPException(status_code=404, detail="Invalid request.")
        cache.delete("recs"+user_id)
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

    @app.post("/search")
    async def search_movies(payload: SearchInput):
        """
        Given the `SearchInput`, a request is made to our
        AWS Elast Search Service instance to get search results.
        """
        result = predictor.search_movies(payload.query)
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
        if result == "Failure":
            raise HTTPException(status_code=404, detail="Invalid request.")
        cache.set("explore"+today, pickle.dumps(result))
        return result

    @app.get("/explore/{user_id}")
    async def explore_user(user_id: str):
        """
        Given a `user_id`, explore data is returned.

        Parameters:
        - **user_id:** str
        """
        # the lists work to a degree but still need a title
        result = cache.get("explore"+user_id)
        if result is not None:
            result = pickle.loads(result)
            return result
        result = predictor.get_recent_recommendations(user_id)
        if result == "Failure":
            raise HTTPException(status_code=404, detail="Invalid request.")
        cache.set("explore"+user_id, pickle.dumps(result))
        return result

    """ Start of Movie List routes """
    @app.post("/movie-list", response_model=MovieList)
    async def create_movie_list(payload: CreateListInput):
        """
        Given a `user_id` and `name`, we create a movie_list and return the 
        `list_id`.

        Parameters:
        - **user_id:** str
        - **name:** str

        Returns:
        - **list_id:** int
        """
        result = predictor.create_movie_list(payload)
        if result == "Failure":
            raise HTTPException(status_code=404, detail="Invalid request.")
        cache.delete("lists"+payload.user_id)
        if not payload.private:
            cache.delete("alllists")
        return result

    @app.get("/movie-list/all", response_model=List[MovieList])
    async def get_all_lists():
        """
        Gets all public movie lists.
        """
        result = cache.get("alllists")
        if result is not None:
            result = pickle.loads(result)
            return result
        result = predictor.get_all_lists()
        if result == "Failure":
            raise HTTPException(status_code=404, detail="Invalid request.")
        cache.set("alllists", pickle.dumps(result))
        return result

    @app.get("/movie-list/all/{user_id}", response_model=List[MovieList])
    async def get_user_lists(user_id: str):
        """
        Given a `user_id`, we grab a preview of all movie lists 
        the user has made.

        Parameters:
        - **user_id:** str

        Returns:
        - List[ListPreview]

        ListPreview Object:
        - list_id: int
        - name: str
        """
        result = cache.get("lists"+user_id)
        if result is not None:
            result = pickle.loads(result)
            return result
        result = predictor.get_user_lists(user_id)
        if result == "Failure":
            raise HTTPException(status_code=404, detail="Invalid request.")
        cache.set("lists"+user_id, pickle.dumps(result))
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
        if result == "Failure":
            raise HTTPException(status_code=404, detail="Invalid request.")
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
        if result == "Failure":
            raise HTTPException(status_code=404, detail="Invalid request.")
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
        if result == "Failure":
            raise HTTPException(status_code=404, detail="Invalid request.")
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
        if result == "Failure":
            raise HTTPException(status_code=404, detail="Invalid request.")
        cache.delete("movielist"+str(list_id))
        cache.delete("lists"+str(result[0]))
        if not result[1]:
            cache.delete("alllists")
        return "Success"
    """ End of Movie List routes """

    return app
