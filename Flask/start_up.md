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