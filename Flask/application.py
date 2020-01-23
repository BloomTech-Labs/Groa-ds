from flask import Flask, session, render_template, request, flash, redirect
import pandas as pd
#from zipfile import ZipFile

import psycopg2
#from getpass import getpass

#self import
from psycopg2_blob import seventoten,query2,id_to_title
from model_functions import ScoringService


application = Flask(__name__)
application.secret_key = 'I would have been your daddy'


@application.route("/")
def index():
    '''
    Main Page, has no real function as of now
    '''
    return render_template("public/index.html")

'''@application.route("/letterboxd_upload", methods=["GET", "POST"])
def letterboxd_upload():

    if request.method == "POST":
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']

        # no file name
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)

        if request.files:

            file = request.files["file"]
            with ZipFile(file, 'r') as zip:
                zip.extractall(path='temp',members=['ratings.csv','reviews.csv'])
            
            ratings = pd.read_csv('temp/ratings.csv', encoding='cp1252')
            reviews = pd.read_csv('temp/reviews.csv')
            #dump ratings and reviews into database and then call model on username. Said username is in the zipfile name<EZ>.
            return render_template('public/upload.html', df=ratings.head())


    return render_template("public/letterboxd_upload.html")'''

@application.route('/imdb_upload')
def imdb_upload():
    '''
    allows you to upload your ratings csv that you got from imdb
    '''
    return render_template('public/imdb_upload.html')

@application.route('/uploader',methods = ['GET','POST'])
def upload_file():
    '''
    the result of the imdb upload, you can see a table of your rated movies and adjust them according to 
    year released and personal rating
    '''
    if request.method == "POST":
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']

        # no file name
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)

        if request.files:

            file = request.files["file"]
            df=pd.read_csv(file)
            #strip beginning ts
            df['Const'] = df['Const'].str.strip('t')
            #dropping what I think to be extraneous 
            df = df.drop(columns=['Title Type','Num Votes','Directors','Genres','URL','Release Date'])
            #get stuff better than 7
            df = df[df['Your Rating'] >= 7]
            session['df']=df.to_json()
            #dump ratings and reviews into database and then call model on username. Said username is in the zipfile name<EZ>.        
            return render_template('public/view.html', name='Watched List',data = df.to_html())
            
@application.route('/updated',methods=['GET','POST'])
def update():
    '''
    updated table from imdb uploader, you can view your revised table and submit your choices to the model
    '''
    #if request.method=='POST':
    df=pd.read_json(session['df'])
    print(df)
    rate_min=int(request.form['rate_min'])
    rate_max=int(request.form['rate_max'])
    year_min=int(request.form['year_min'])
    year_max=int(request.form['year_max'])
    
    df=df[(df['Year']>year_min) & (df['Year']<year_max)]
    df=df[(df['Your Rating']>rate_min) & (df['Your Rating']<rate_max)]
    session['df']=df.to_json()

    return render_template('public/updated.html', data = df.to_html())
        
@application.route('/submission',methods=['POST'])
def submit():
    '''
    Shows recommendations from your IMDB choices
    '''
    model = ScoringService()
    model.get_model()
    #need to configure input for current model but ulitmately may not need to for updated model
    df=pd.read_json(session['df'])
    predictions = model.predict(df)
    df2 = pd.DataFrame(predictions, columns = ['Movie_id', 'Percent_match'])
    return render_template('public/recommendations.html', df=df2)

@application.route('/recommendations', methods=['GET', 'POST'])
def recommend():
    '''
    gives recommendations based on reviews in our db given an username
    '''
    if request.method == 'POST':
        username = request.form['name']
        movie_list = query2(username)
        model = ScoringService()
        model.get_model()
        
        predictions = model.predict(movie_list)
        df = pd.DataFrame(predictions, columns = ['Movie_id','Percent_match'])
        
        return render_template('public/recommendations.html', df=df)
    elif request.method == 'GET':
        return render_template('public/recommendation_form.html')
        

@application.route('/manualreview', methods=['GET', 'POST'])
def review():
    '''
    Unfinished, lets a user input a review manually
    '''
    if request.method == 'POST':
        #gets these things from user
        title = request.form['title']
        review_title = request.form['review_title']
        review_text = request.form['review']
        user_rating = request.form['rating']
        username = request.form['username']
        '''create new review entry, first querying movie_id from movie_title,
        then adding the above, along with the day's date, into the reviews table.
        It would be generating id and zeros for the two helpful things.'''
        #dropdown of post sucessful!


@application.route('/watchhistory')
def watchhistory():
    #checkout the twitoff app to do /watchhistory/user

    '''start scraper on user's rating page to get rated movies because
    for us, rating = watched. If user's ratings are private, return message to 
    please make ratings public. That's probably better than asking for their login info.
    '''
    #display scraped data? display whether they've actually reviewed it and if not, have a link to redirect to review page?
    
if __name__ == "__main__":
    application.run(port=5000, debug=True)