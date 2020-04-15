from fastapi import FastAPI
from pydantic import BaseModel
from apps.util import PythonPredictor

app = FastAPI(
    title="groa-ds-api",
    description="Movie recommendations based on user ratings and preferences using a trained w2v model",
    version="1.0"
)

predictor = PythonPredictor()

class RecData(BaseModel):
    user_id: int
    # one or the other (i want to use n but it was number_of_re.. prior)
    n: int = 20
    number_of_recommendations: int = 20
    good_threshold: int = None
    bad_threshold: int = None
    harshness: int = None

def create_app():
    
    @app.get("/")
    async def index():
        welcome_message = "This is the DS API for Groa"
        return welcome_message

    @app.post("/recommendation")
    async def recommend(payload: RecData):
        payload = request.get_json(force=True)
        result = predictor.predict(payload)
        return result

    return app
