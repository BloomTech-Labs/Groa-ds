from fastapi import FastAPI
from pydantic import BaseModel
from w2v_helpers import Recommender
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


class RecData(BaseModel):
    user_id: int
    # one or the other (i want to use n but it was number_of_re.. prior)
    n: int = 10
    number_of_recommendations: int = 10
    good_threshold: int = None
    bad_threshold: int = None
    harshness: int = None


class SimData(BaseModel):
    movie_id: str


def create_app():
    
    @app.get("/")
    async def index():
        welcome_message = "This is the DS API for Groa"
        return welcome_message

    @app.post("/recommendation")
    async def recommend(payload: RecData):
        result = predictor.get_recommendations(payload)
        return result
    
    @app.post("/similar-movies")
    async def similar_movies(payload: SimData):
        response = f"Need to serve similar movies to {payload.movie_id}"
        return response

    return app
