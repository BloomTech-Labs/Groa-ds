# Test Locally
- live on http://a53907b2c534911ea8bbd0a1babb722b-2078997105.us-west-2.elb.amazonaws.com/movie-recommender
- On Windows replace *** with database password and run this in the terminal
```
set DB_PASSWORD=***
```

- On Mac/Linux
```
export DB_PASSWORD=***
```
- run ipython terminal to test 

```
ipython 
> from predictor import PythonPredictor
> predictor.predict('{ "0": "116282", "1": "2042568", "2": "1019452", "3": "1403865" }')
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

