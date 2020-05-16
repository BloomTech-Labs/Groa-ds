from elasticsearch import Elasticsearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
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
# test search 
result = es.search(index="groa", size=20, expand_wildcards="all", body={
    "query": {
        "fuzzy" : { 
            "primary_title" : {
                "value": "lord"
            }
        }
    }
})
print("Test Search of 'lord'")
print(result)