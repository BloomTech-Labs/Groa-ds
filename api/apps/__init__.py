from fastapi import FastAPI
from pydantic import BaseModel
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

    @app.get("/stats/decades/{user_id}")
    async def get_stats_by_decade(user_id):
        df = predictor.get_user_data(user_id)
        df["decade"] = df["year"].apply(lambda x: x//10*10)
        first_decade = df["decade"].min()
        last_decade = df["decade"].max()
        dec_to_count = {dec: 0 for dec in range(first_decade, last_decade+1, 10)}
        for dec in df["decade"].values:
            dec_to_count[dec] += 1
        return dec_to_count

    return app
