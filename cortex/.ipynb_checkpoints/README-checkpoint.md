# Deploy using Cortex.dev service:

- The EKS and Docker based CLI service expects a predictor.py file with a PythonPredictor class with 'config'
as an argument with a predict function to be called each time there is a 'JSON' post
request to the endpoint, returning a set of 'predictions'.

- This folder starts at about 50kb and about 200mb are downloaded and unzipped when the class is initiated. 

- Credentials for the database and s3 bucket are stored in a values.json file.

- BEFORE pushing to github make sure that "values.json" is blank or deleted or listed in gitignore or on a private repo.  

# Testing predictor.py
- config is required for Cortex deployment 
- payload is currently just a user id number/string
- output is two recommendation ids and two recommendation JSON strings

# Testing AWS credentials with Boto3
- follow step one of this guide https://aws.amazon.com/getting-started/tutorials/backup-to-s3-cli/
    - to create an AWS IAM user to allow programmatic access  
    - download the credentials.csv and put the keys below 
