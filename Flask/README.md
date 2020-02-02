# Flask App Documentation <img align="right" src="https://www.clipartkey.com/mpngs/m/145-1450071_flask-python-logo-transparent.png" width="120" height="120">
[Deployment Link]()
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
**/**: Landing Page. Description of the app and its purpose.

**/letterboxd_upload**: User can upload a zipped file of Letterboxd export data.

**/imdb_upload**: User can upload a ratings.csv file of IMDb ratings export data.

**/letterboxd_submission**: 

User can:
   - see a summary of their movies.
   - indicate the ranges of ratings they give to movies they like and dislike.
   - choose to receive recommendations for hidden gems (well-regarded, under-discovered movies). Only available if the user provides reviews.
   - choose to receive recommendations for cult movies (movies considered underrated by similar reviewers). Only available if the user provides reviews.
   - choose whether the recommender should place special weight on movies the user has given especially high or low ratings.
   - submit their choices to begin the recommendation process.

**/imdb_submission**: 
User can:
   - see a summary of their movies.
   - indicate the ranges of ratings they give to movies they like and dislike.
   - choose whether the recommender should place special weight on movies the user has given especially high or low ratings.
   - submit their choices to begin the recommendation process.

**/letterboxd_recommendations**:
User can:
   - see a list of up to 100 movie recommendations from the w2v Recommender model (user-based collaborative filtering), complete with info about those movies.
   - see, if requested, a list of hidden gems and/or cult movies recommended by the r2v Recommender model (review-based).
   - download a CSV of their recommendations via a popup window.
   - give positive and negative feedback on the recommendations, and submit the feedback for an improved list.
   
 **/imdb_recommendations**:
 User can:
   - see a list of up to 100 movie recommendations from the w2v Recommender model (user-based collaborative filtering), complete with info about those movies.
   - download a CSV of their recommendations via a popup window.
   - give positive and negative feedback on the recommendations, and submit the feedback for an improved list.

**/resubmission**:
User can:
   - see an updated list of up to 500 movie recommendations from the w2v Recommender model (user-based collaborative filtering), complete with info about those movies.
   - download a CSV of their recommendations.
   - continue to submit feedback for new recommendations, indefinitely.
   
**/userlookup**:
User can:
   - enter IMDb username with the aid of an autocompleting list of usernames in the database.
   - view the watch history of an IMDb user if they exist in the database.

## Run Locally <a name="local"></a>
### Step 1:
Before starting anything, make sure to activate the virtual environment. [Set up your virtual environment](https://www.liquidweb.com/kb/how-to-setup-a-python-virtual-environment-on-windows-10/) and then [install the needed imports from the requirements file](https://stackoverflow.com/questions/48787250/set-up-virtualenv-using-a-requirements-txt-generated-by-conda). From then on, call source <\your virtual environment folder>\/Scripts/activate to start up the environment if your are in Windows. Other systems should call <\your virtual environment folder>\/bin/activate.

### Step 2:
In order to run the flask app, first you need to set it to the right file. 
In Windows, we go: set FLASK_APP=application.py.
In other systems, we go: export FLASK_APP=application.py.

### Step 3:
Now that flask knows which file to run, type in 'flask run'

### Optional Step 4:
If you want to be in debug mode: export FLASK_ENV=development
In Windows, replace export with set

### Optional Step 5:
If you don't like doing step 2 or step 4 every time, you can make a .flaskenv file and put "FLASK_APP = application.py
FLASK_ENV = development" in it. Very nice!
## Deployment Instruction for AWS Elastic Beanstalk <a name="deployment"></a>
### GUI Upload <a name="gui"></a>
[Elastic Beanstalk Upload Guide](https://medium.com/analytics-vidhya/deploying-a-flask-app-to-aws-elastic-beanstalk-f320033fda3c)
### Step 1(Windows):
First go to your AWS console
type bean in the search and select elastic beanstalk
On the elastic beanstalk page you go to create new application on the top right of the page
### Step 2(Windows):
Give it a name and a description if you want to and then press create
Then it will bring you to a new page that will say "No environments currently exist for this application. Create one now." Click on create one now
Select web server environment
### Step 3(Windows):
Give it a name, domain and description (if you want to), on platform under preconfigured platform choose python, and on apllication code leave it at sample application (You can do the upload of your zipfile here if you choose the third option). Then create environment.
It will start creating the environment. Mine took about 3 minute to create.
### Step 4(Windows):
Click on your application on the top bar and navigate to your environment. It will bring you to the dashboard. If you need to set environment variables (like passwords), navigate to Configuration, click Modify for the Software category, and then enter the key pair in Environment properties at the bottom of the page. Otherwise, you can upload the zipfile of your flask app. 

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
[Flask](https://flask.palletsprojects.com/en/1.1.x/)[Pandas](https://pandas.pydata.org/pandas-docs/stable/)[Gensim](https://radimrehurek.com/gensim/auto_examples/index.html)[Psycopg2](https://www.psycopg.org/docs/)[AWS Elastic Beanstalk](https://docs.aws.amazon.com/elastic-beanstalk/index.html)
## What's Next <a name="next"></a>




