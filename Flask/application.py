from flask import Flask, session, render_template, request, flash, redirect
import pandas as pd
from zipfile import ZipFile

import psycopg2
# from getpass import getpass

# self import
from psycopg2_blob import seventoten,query2,id_to_title
from w2v_inference import *


application = Flask(__name__)
application.secret_key = 'secret_bee'

# where we store large files for global access
df_global = None
ratings_global = None
reviews_global = None
watched_global = None
watchlist_global = None

@application.route("/")
def index():
    '''
    Main Page, has no real function as of now
    '''
    return render_template("public/index.html")

@application.route("/letterboxd_upload", methods=["GET", "POST"])
def letterboxd_upload():
    '''
    allows you to upload your ratings csv that you got from imdb
    '''
    return render_template('public/letterboxd_upload.html')

@application.route('/letterboxd_uploaded', methods=['GET','POST'])
def lb_uploaded():
    '''
    next step for letterboxd, this page gets the zipfile from the previous page, extracts four csvs and commits them
    to the session. HTML wise, this page presents two sliders that are used by the model
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
            with ZipFile(file, 'r') as zip:
                zip.extractall(path='temp',members=['ratings.csv','reviews.csv','watchlist.csv','watched.csv'])
            
            ratings = pd.read_csv('temp/ratings.csv', encoding='cp1252')
            reviews = pd.read_csv('temp/reviews.csv')
            watched = pd.read_csv('temp/watched.csv')
            watchlist = pd.read_csv('temp/watchlist.csv')
            
            session['ratings'] = ratings.to_json()
            session['reviews'] = reviews.to_json()
            session['watched'] = watched.to_json()
            session['watchlist'] = watchlist.to_json()
            return render_template('public/letterboxd_uploaded.html', data=ratings.head().to_html())

@application.route('/letterboxd_submission', methods=['GET', 'POST'])
def lb_submit():
    '''
    Shows recommendations from your Letterboxd choices
    '''
    ratings = ratings_global
    watched = watched_global
    watchlist = watchlist_global
    bad_rate = int(request.form['bad_rate']) / 2
    good_rate = int(request.form['good_rate']) / 2
    # connect
    s = Recommender('w2v_limitingfactor_v1.model')
    s.connect_db()
    # import user data

    # prep user data
    good_list, bad_list, hist_list, val_list = prep_data(
                                        ratings, watched, watchlist, good_threshold=good_rate, bad_threshold=bad_rate)


    recs = pd.DataFrame(s.predict(good_list, bad_list, hist_list, val_list, n=100, harshness=1, scoring=False),
                        columns=['Title', 'Year', 'URL', 'Avg. Rating', '# Votes', 'Similarity Score'])
    return render_template('public/recommendations.html', df=recs, tables=[recs.to_html(classes='data')], titles=recs.columns.values)

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
            try:
                df=pd.read_csv(file, encoding='cp1252')
            except:
                df=pd.read_csv(file, encoding='latin1')
            #strip beginning ts
            df['Const'] = df['Const'].str.strip('t')
            #dropping what I think to be extraneous
            df = df.drop(columns=['Title Type','Num Votes','Directors','Genres','URL','Release Date'])
            # df = df.rename(columns={'Your Rating':'Rating','Title':'Name','Const':'Movie ID'})
            #get stuff better than 7
            #df = df[df['Your Rating'] >= 7]
            # session['df']= df.to_json()
            global df_global
            df_global = df.to_json()
            #dump ratings and reviews into database and then call model on username. Said username is in the zipfile name<EZ>.
            return render_template('public/view.html', name='Watched List',data = df.to_html())

@application.route('/submission',methods=['GET','POST'])
def submit():
    '''
    Shows recommendations from your IMDB choices
    '''

    #need to configure input for current model but ulitmately may not need to for updated model
    df=pd.read_json(df_global)
    bad_rate=int(request.form['bad_rate'])/2
    good_rate=int(request.form['good_rate'])/2
    #year_min=int(request.form['year_min'])
    #year_max=int(request.form['year_max'])
    #connect
    s = Recommender('w2v_limitingfactor_v1.model')
    s.connect_db()
    # import user data


    # prep user data
    good_list, bad_list, hist_list, val_list = prep_data(
                                        df, good_threshold=good_rate, bad_threshold=bad_rate)

    recs = pd.DataFrame(s.predict(good_list, bad_list, hist_list, val_list, n=100, harshness=1, scoring=False),
                        columns=['Title', 'Year', 'URL', 'Avg. Rating', '# Votes', 'Similarity Score'])
    return render_template('public/recommendations.html', df=recs, tables=[recs.to_html(classes='data')], titles=recs.columns.values)

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
