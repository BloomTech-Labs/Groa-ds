from elasticsearch import Elasticsearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
import psycopg2
from dotenv import load_dotenv
load_dotenv()
import os
import time


#connect to our cluster
es = Elasticsearch(
    hosts=[{'host': os.getenv('ELASTIC'), 'port': 443}],
    http_auth=AWS4Auth(os.getenv('ACCESS_ID'), os.getenv('ACCESS_SECRET'), 'us-east-1', 'es'),
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection
)
print(es.cluster.health())
# connect to our DB
conn = psycopg2.connect(
    database=os.getenv('DB_NAME'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    host=os.getenv('HOST'),
    port=os.getenv('PORT')
)

# get movies info
curs = conn.cursor()
query = "SELECT movie_id, primary_title, original_title, start_year, genres, description FROM movies;"
curs.execute(query)
movies = curs.fetchall()
movie_count = len(movies)
counter = 0
exception_count = 0

print("Starting to load all movies...")
for movie in movies:
    try:
        es.index(index='groa', doc_type='movies', id=movie[0], body={
            "primary_title": movie[1],
            "original_title": movie[2],
            "year": movie[3],
            "genres": movie[4].split(","),
            "description": movie[5]
        })
        counter += 1
        if counter % 100 == 0:
            print("Current counter:", counter)
    except Exception as e:
        print(e)
        print(exception_count, counter)
        time.sleep(2)
        exception_count += 1
        if exception_count % 5 == 0:
            es = Elasticsearch(
                hosts=[{'host': os.getenv('ELASTIC'), 'port': 443}],
                http_auth=AWS4Auth(os.getenv('ACCESS_ID'), os.getenv('ACCESS_SECRET'), 'us-east-1', 'es'),
                use_ssl=True,
                verify_certs=True,
                connection_class=RequestsHttpConnection
            )

# test search 
result = es.search(index="groa", body={
    "query": {
        "fuzzy" : { 
            "primary_title" : {
                "value": "star wars"
            }
        }
    }
})
print("Test Search of 'star wars'")
print(result)