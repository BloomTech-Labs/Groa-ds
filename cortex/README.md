# Cortex Deployment 

- To deploy with Cortex create a values.json file in this folder with database credentials and programmatic s3 bucket access keys and change the cluster name and s3 bucket in cluster.yaml to match yours. 

## movie-ratings-recommender
- curl http://a56a5b3d360b111ea906516f7da0429b-156937678.us-east-1.elb.amazonaws.com/movie-ratings-recommender?debug=true -X POST -H "Content-Type: application/json" -d @sample.json

## movie-reviews-recommender 
- curl http://a56a5b3d360b111ea906516f7da0429b-156937678.us-east-1.elb.amazonaws.com/movie-reviews-recommender?debug=true -X POST -H "Content-Type: application/json" -d @sample2.json

### sample.json files
```
{
"user_id": 1,
"number_of_recommendations": 50,
"good_threshold": 5,
"bad_threshold": 4,
"harshness": 1
}
```

### sample2.json
```
{
"user_id": 5028,
"number_of_recommendations": 1000,
"good_threshold": 3,
"bad_threshold": 2,
"harshness": 1
}