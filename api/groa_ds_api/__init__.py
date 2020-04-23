from fastapi import BackgroundTasks, FastAPI
from groa_ds_api.utils import Recommender
from groa_ds_api.models import RecInput, RecOutput, SimInput, SimOutput, ScraperInput
from web_scraping.util import run_scrapers, run_scrapers_update
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


def create_app():

    @app.get("/")
    async def index():
        """
        Simple 'hello' from our API.
        """
        welcome_message = "This is the DS API for Groa"
        return welcome_message

    @app.post("/recommendations", response_model=RecOutput)
    async def get_recommendations(payload: RecInput):
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
        result = predictor.get_recommendations(payload)
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

    @app.post("/scrape-update")
    async def scrape_update(payload: ScraperInput, background_tasks: BackgroundTasks):
        background_tasks.add_task(run_scrapers_update, payload.start, payload.end)
        return "Scrape update started"

    @app.post("/scrape")
    async def scrape(payload: ScraperInput, background_tasks: BackgroundTasks):
        background_tasks.add_task(run_scrapers, payload.start, payload.end)
        return "Scrape update finished"


    return app
