# Deploy using Cortex.dev service:
    --------------------------------

- The EKS and Docker based CLI service expects a predictor.py file with a PythonPredictor class with 'config'
as an argument with a predict function to be called each time there is a 'JSON' post
request to the endpoint, returning a set of 'predictions'.

- This folder starts at about 50kb and about 200mb are downloaded and unzipped when the class is initiated. 

- Credentials for the database and s3 bucket are stored in a values.json file.

- BEFORE pushing to github make sure that "values.json" is blank or deleted or listed in gitignore or on a private repo.  

