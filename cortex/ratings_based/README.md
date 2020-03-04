- The API takes in a user_id and returns a recommendation_id, the recommendation_json is commited to the recommendations table in the database.
- Right now it only is querying for user letterboxd ratings, watchlist and watched from the database, not IMDB data. 


# live 
- http://ace1034515a4911ea8ecd028f1b5a1bc-1712147317.us-east-1.elb.amazonaws.com/movie-recommender

# test
``` 
curl -X POST -H "Content-Type: application/json" -d "1111" http://http://ace1034515a4911ea8ecd028f1b5a1bc-1712147317.us-east-1.elb.amazonaws.com/movie-recommender?debug=true
```

# Test Locally

- On Windows replace *** with database password and host run this in the terminal
```
set DB_PASSWORD=***
set DEV=***
```

- On Mac/Linux
```
export DB_PASSWORD=***
export DEV=***
```
- run ipython terminal to test 

```
ipython 
> from predictor import PythonPredictor
> predictor = PythonPredictor()
> predictor.predict(1111)
```

# Deploy with Cortex 

## Create Virtual Computer 
- Create EC2 T3 instance on AWS 
- On windows: use PuTTY to connect https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/putty.html

## Install Docker 
```
sudo yum update -y
sudo amazon-linux-extras install docker
sudo service docker start
sudo usermod -a -G docker ec2-user
```
- Exit terminal and create a new window to verify commands work
``` 
docker info
```
## Install Git CLI

```
sudo yum install git -y
```
- clone and enter this repo after you install 

## Install Cortex  CLI

```
bash -c "$(curl -sS https://raw.githubusercontent.com/cortexlabs/cortex/0.13/get-cli.sh)"
```
## Set AWS environment variables 

```
export AWS_ACCESS_KEY_ID=******
export AWS_SECRET_ACCESS_KEY=******
```


- check variables 
```
printenv
```

- run cluster and deploy model 
```
cortex cluster up --config=cluster.yaml
cortex deploy

```
# find the API endpoint and test a POST
```
cortex get movie-recommender 
# it will give you info here <API ENDPOINT>
curl -X POST -H "Content-Type: application/json" \
  -d '{ "0": "116282", "1": "2042568", "2": "1019452", "3": "1403865" }'\
 <API ENDPOINT>
 ```

