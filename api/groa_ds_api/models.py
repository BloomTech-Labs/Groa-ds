from pydantic import BaseModel
from typing import List
"""
These are request and response models used by
FastAPI to monitor/enforce the data types of the
JSON requests and responses.
"""

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