# Flask App Documentation <img align="right" src="https://www.clipartkey.com/mpngs/m/145-1450071_flask-python-logo-transparent.png" width="120" height="120">
[Deployement Link]()
# Table of Contents
1. [Quick Rundown](#sum)
2. [Flask App Endpoints](#endpoints)
3. [Run Locally](#local)
4. [Deployment on AWS EB](#deployment)
    * [GUI Upload](#gui)
    * [CLI Upload](#cli)
5. [Built With](#dependency)
6. [What's Next](#next)
## Quick Rundown  <a name="sum"></a>
This flask app's purpose is to serve as an environment for displaying recommendations to a user.
## Flask App Endpoints <a name="endpoints"></a>
The app really does two things at this point. It let's you upload a file from either imdb or letterboxd and it will give you recommendations from the model.
## Run Locally <a name="local"></a>
Server will be and accessible at http://127.0.0.1:5000/ 
## Deployment Instruction for AWS Elastic Beanstalk <a name="deployment"></a>
### GUI Upload <a name="gui"></a>
[Elastic Beanstalk Upload Guide](https://medium.com/analytics-vidhya/deploying-a-flask-app-to-aws-elastic-beanstalk-f320033fda3c)
#### Step 1:
Zip all flask files including hidden folder `.ebextensions`,`.env` file and `requirements.txt`.
#### Step 2: 
Go to terminal and go to your folder where the zip flask file is in.
Run `zip -d flask_app.zip __MACOSX/\*` 
#### Step 3:
Go to your EB environment and upload your flask zip file
### CLI Upload <a name="cli"></a>
Coming Soon
## Built With <a name="dependency"></a>
## What's Next <a name="next"></a>


Before starting anything, make sure to activate the virtual environment. Do this with 'source groavirt/Scripts/activate'

In order to run the flask app, first you need to set it to the right file. 
In Windows, we go: set FLASK_APP=application.py.
In other systems, we go: export FLASK_APP=application.py.
Now that flask knows which file to run, type in 'flask run'
If you want to be in debug mode: export FLASK_ENV=development
In window, replace export with set


Setting up Beanstalk:
First go to your console
type bean in the search and select elastic beanstalk
on the elastic beanstalk page you go to create new application on the top right of the page
Give it a name and a description if you want to and then press create
Then it will bring you to a new page that will say "No environments currently exist for this application. Create one now." Click on create one now
Select web server environment
Give it a name, domain and description (if you want to), on platform under preconfigured platform choose python, and on apllication code leave it at sample application. Then create environment.
It will start creating the environment. Mine took about 3 minute to create.
Click on your application on the top bar and navigate to your environment. It will bring you to the dashboard. If you need to set environment variables (like passwords), use Tags at the bottom of the left side menu. Otherwise, you can upload the zipfile of your flask app. 

That brings us to a new part, Setting up the zipfile: consult: https://medium.com/analytics-vidhya/deploying-a-flask-app-to-aws-elastic-beanstalk-f320033fda3c
If you're on windows, get into the flask folder, cntrl-A to select everything, then right click and select send to zipfile.
Then go back to beanstalk, select upload and deploy, and select the zipfile you just made. I think that's everything.