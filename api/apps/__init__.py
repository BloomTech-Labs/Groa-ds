from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from apps.utils import Recommender
import os
from pathlib import Path

app = FastAPI(
    title="groa-ds-api",
    description="Movie recommendations based on user ratings and preferences using a trained w2v model",
    version="1.0"
)

parent_path = Path(__file__).resolve().parents[1]
model_path = os.path.join(parent_path, 'w2v_limitingfactor_v2.model')

predictor = Recommender(model_path)


class Movie(BaseModel):
    movie_id: str 
    score: float 
    title: str 
    year: int 
    genres: List[str]
    poster_url: str


class RecInput(BaseModel):
    user_id: int
    num_recs: int = 10
    good_threshold: int = None
    bad_threshold: int = None
    harshness: int = None


class RecOutput(BaseModel):
    recommendation_id: str 
    data: List[Movie]


class SimInput(BaseModel):
    movie_id: str
    num_movies: int = 10


class SimOutput(BaseModel):
    data: List[Movie]


def create_app():
    
    @app.get("/")
    async def index():
        welcome_message = "This is the DS API for Groa"
        return welcome_message

    @app.post("/recommendations", response_model=RecOutput)
    async def get_recommendations(payload: RecInput):
        result = predictor.get_recommendations(payload)
        return result
    
    @app.post("/similar-movies", response_model=SimOutput)
    async def get_similar_movies(payload: SimInput):
        result = predictor.get_similar_movies(payload)
        return result

    @app.get("/stats/decades/{user_id}")
    async def get_stats_by_decade(user_id):
        # df = predictor.get_user_data(user_id)
        # df["decade"] = df["year"].apply(lambda x: x//10*10)
        # first_decade = df["decade"].min()
        # last_decade = df["decade"].max()
        # dec_to_count = {dec: 0 for dec in range(first_decade, last_decade+1, 10)}
        # for dec in df["decade"].values:
        #     dec_to_count[dec] += 1
        return "New class needs to be built for user_data"

    return app
