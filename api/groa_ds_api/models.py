from pydantic import BaseModel
from typing import List
"""
These are request and response models used by
FastAPI to monitor/enforce the data types of the
JSON requests and responses.
"""


class MovieRec(BaseModel):
    movie_id: str
    score: float
    title: str
    year: int
    genres: List[str]
    poster_url: str
    trailer_url: str 
    avg_rating: float 
    description: str


class Movie(BaseModel):
    movie_id: str
    title: str
    year: int
    genres: List[str]
    poster_url: str
    trailer_url: str 
    avg_rating: float 
    description: str


class MovieList(BaseModel):
    list_id: int
    name: str
    private: bool


class Provider(BaseModel):
    provider_id: int
    name: str
    logo: str
    link: str
    presentation_type: str
    monetization_type: str


class RecInput(BaseModel):
    user_id: str
    num_recs: int = 10
    good_threshold: int = 4
    bad_threshold: int = 3
    harshness: int = 1


class RecOutput(BaseModel):
    data: List[MovieRec]


class SimInput(BaseModel):
    movie_id: str
    num_movies: int = 10


class SimOutput(BaseModel):
    data: List[MovieRec]


class ProviderOutput(BaseModel):
    data: List[Provider]


class CreateListInput(BaseModel):
    user_id: str
    name: str
    private: bool = False


class GetListOutput(BaseModel):
    data: List[Movie]
    recs: List[MovieRec]


class ExploreOutput(BaseModel):
    data: List[Movie]


class RatingInput(BaseModel):
    movie_id: str
    user_id: str
    rating: float


class UserAndMovieInput(BaseModel):
    movie_id: str 
    user_id: str


class SearchInput(BaseModel):
    query: str


class SearchOutput(BaseModel):
    data: List[Movie]