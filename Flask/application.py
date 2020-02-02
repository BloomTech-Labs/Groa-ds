from flask import Flask, session, render_template, request, flash, redirect
from flask_session import Session
import pandas as pd
import numpy as np
from zipfile import ZipFile
import json
import os, shutil

import psycopg2
# from getpass import getpass

# self import
from psycopg2_blob import seventoten,query2,id_to_title,get_imdb_users
from w2v_inference import *
from r2v_inference import *


application = Flask(__name__)
application.secret_key = 'secret_bee'
SESSION_TYPE = 'filesystem'
application.config.from_object(__name__)
Session(application)



@application.route("/")
def index():
    '''
    Main Page, has no real function as of now
    '''
    return render_template("public/Homepage.html")

@application.route("/letterboxd_upload", methods=["GET", "POST"])
def letterboxd_upload():
    '''
    allows you to upload your ratings csv that you got from imdb
    '''
    return render_template('public/letterboxd_upload.html')

@application.route('/letterboxd_submission', methods=['GET','POST'])
def lb_submit():
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
            tag = str(np.random.uniform())
            with ZipFile(file, 'r') as zip:
                zip.extractall(path=f'temp{tag}',members=['ratings.csv','reviews.csv','watchlist.csv','watched.csv'])


            ratings = pd.read_csv(f'temp{tag}/ratings.csv', encoding='cp1252')
            reviews = pd.read_csv(f'temp{tag}/reviews.csv')
            watched = pd.read_csv(f'temp{tag}/watched.csv')
            watchlist = pd.read_csv(f'temp{tag}/watchlist.csv')

            session['ratings'] = ratings.to_json()
            session['reviews'] = reviews.to_json()
            session['watched'] = watched.to_json()
            session['watchlist'] = watchlist.to_json()

            shutil.rmtree(f'temp{tag}')

            return render_template('public/letterboxd_submission.html', data=ratings.head().to_html(index=False))

@application.route('/letterboxd_recommendations', methods=['GET', 'POST'])
def lb_recommend():
    '''
    Shows recommendations from your Letterboxd choices
    '''
    ratings = pd.read_json(session['ratings'])
    reviews = pd.read_json(session['reviews'])
    watched = pd.read_json(session['watched'])
    watchlist = pd.read_json(session['watchlist'])
    bad_rate = int(request.form['bad_rate']) / 2
    good_rate = int(request.form['good_rate']) / 2
    hidden = "hidden" in request.form
    cult = "cult" in request.form

    # connect
    s = Recommender('w2v_limitingfactor_v1.model')
    s.connect_db()
    r = r2v_Recommender('r2v_Botanist_v1.1000.5.model')
    r.connect_db()
    # import user data

    # prep user data
    good_list, bad_list, hist_list, val_list, ratings_dict = prep_data(
                                        ratings, watched, watchlist, good_threshold=good_rate, bad_threshold=bad_rate)

    recs = pd.DataFrame(s.predict(good_list, bad_list, hist_list, val_list, ratings_dict, n=100, harshness=1, scoring=False),
                        columns=['Title', 'Year', 'URL', 'Avg. Rating', '# Votes', 'Similarity Score','Movie ID'])
    reviews = prep_reviews(reviews)

    def links(x):
        '''Changes URLs to actual links'''
        return '<a href="%s">Go to the IMDb page</a>' % (x)


    hidden_df = pd.DataFrame(columns=['Title', 'Year', 'URL', '# Votes', 'Avg. Rating',
            'User Rating', 'Reviewer', 'Review', 'Movie ID'])
    cult_df = pd.DataFrame(columns=['Title', 'Year', 'URL', '# Votes', 'Avg. Rating',
            'User Rating', 'Reviewer', 'Review', 'Movie ID'])

    if hidden or cult:
        if cult:
            cult_results, hidden_results = r.predict(reviews, hist_list=hist_list)
            cult_df = pd.DataFrame(cult_results,
                columns=['Title', 'Year', 'URL', '# Votes', 'Avg. Rating',
                        'User Rating', 'Reviewer', 'Review', 'Movie ID'])
            cult_df['URL'] = cult_df['URL'].apply(links)
            cult_df['Vote Up'] = '<input type="checkbox" name="upvote" value=' \
                + cult_df['Movie ID'] + '>  Good idea<br>'
            cult_df['Vote Down'] = '<input type="checkbox" name="downvote" value=' \
                + cult_df['Movie ID'] + '>  Hard No<br>'
        if hidden:
            hidden_df = pd.DataFrame(hidden_results,
                columns=['Title', 'Year', 'URL', '# Votes', 'Avg. Rating',
                        'User Rating', 'Reviewer', 'Review', 'Movie ID'])
            hidden_df['URL'] = hidden_df['URL'].apply(links)
            hidden_df['Vote Up'] = '<input type="checkbox" name="upvote" value=' \
                + hidden_df['Movie ID'] + '>  Good idea<br>'
            hidden_df['Vote Down'] = '<input type="checkbox" name="downvote" value=' \
                + hidden_df['Movie ID'] + '>  Hard No<br>'

    recs['URL'] = recs['URL'].apply(links)
    recs['Vote Up'] = '<input type="checkbox" name="upvote" value=' \
        + recs['Movie ID'] + '>  Good idea<br>'
    recs['Vote Down'] = '<input type="checkbox" name="downvote" value=' \
        + recs['Movie ID'] + '>  Hard No<br>'
    id_list = recs['Movie ID'].to_list()
    recs = recs.drop(columns='Movie ID')

    session.clear()
    session['id_list']=json.dumps(id_list)
    session['good_list']=json.dumps(good_list)
    session['bad_list']=json.dumps(bad_list)
    session['hist_list']=json.dumps(hist_list)
    session['val_list']=json.dumps(val_list)

    session['ratings_dict']=json.dumps(ratings_dict)
    session['good_rate']=good_rate
    session['bad_rate']=bad_rate
    return render_template('public/Groa_recommendations.html',
                            data=recs.to_html(index=False,escape=False),
                            hidden_data=hidden_df.to_html(index=False,escape=False),
                            cult_data=cult_df.to_html(index=False,escape=False))

@application.route('/resubmission',methods=['POST'])
def resubmit():
    '''
    This page takes the ids from the recommedation page that the user liked and adds them to
    '''
    try:
        checked_list = json.loads(session['checked_list'])
    except:
        checked_list = []
    try:
        rejected_list = json.loads(session['rejected_list'])
    except:
        rejected_list = []
    checked_list.extend(request.form.getlist('upvote')) # log upvotes
    rejected_list.extend(request.form.getlist('downvote')) # log downvotes
    id_list = json.loads(session['id_list']) # all of the ids of the previous recommendations
    good_list = json.loads(session['good_list'])

    bad_list = json.loads(session['bad_list'])
    hist_list = json.loads(session['hist_list'])
    val_list = json.loads(session['val_list'])
    ratings_dict = json.loads(session['ratings_dict'])

    s = Recommender('w2v_limitingfactor_v1.model')
    s.connect_db()

    recs = pd.DataFrame(s.predict(good_list, bad_list, hist_list, val_list,
                ratings_dict, checked_list, rejected_list, n=500, harshness=1, scoring=False),
                columns=['Title', 'Year', 'URL', 'Avg. Rating', '# Votes',
                'Similarity Score','Movie ID'])
    def links(x):
        '''Changes URLs to actual links'''
        return '<a href="%s">Go to the IMDb page</a>' % (x)

    recs['URL'] = recs['URL'].apply(links)
    recs['Vote Up'] = '<input type="checkbox" name="upvote" value=' \
            + recs['Movie ID'] + '>  Good idea<br>'
    recs['Vote Down'] = '<input type="checkbox" name="downvote" value=' \
        + recs['Movie ID'] + '>  Hard No<br>'

    id_list2 = recs['Movie ID'].to_list()

    session['id_list'] = json.dumps(id_list2)
    session['checked_list'] = json.dumps(checked_list)
    session['rejected_list'] = json.dumps(rejected_list)

    recs.drop(columns='Movie ID')

    return render_template('public/re_recommendations.html',
                            data=recs.to_html(escape=False,index=False))

@application.route('/imdb_upload')
def imdb_upload():
    '''
    allows you to upload your ratings csv that you got from imdb
    '''
    return render_template('public/imdb_upload.html')

@application.route('/imdb_submission',methods = ['GET','POST'])
def imdb_submit():
    '''
    the result of the imdb upload, you can see a table of your rated movies
    and adjust them according to year released and personal rating
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
            df = df.drop(columns=['Title Type','Num Votes','Directors','Genres',
                                    'URL','Release Date'])
            session['df']= df.to_json()
            # dump ratings and reviews into database and then call model on username.
            # Said username is in the zipfile name<EZ>.
            return render_template('public/imdb_submission.html',
                    name='Watched List',data = df.head().to_html(index=False))

@application.route('/imdb_recommendations',methods=['GET','POST'])
def submit():
    '''
    Shows recommendations from your IMDB choices
    '''

    #need to configure input for current model but ulitmately may not need to for updated model
    df = pd.read_json(session['df'])
    bad_rate = int(request.form['bad_rate'])/2
    good_rate = int(request.form['good_rate'])/2
    #year_min=int(request.form['year_min'])
    #year_max=int(request.form['year_max'])
    #connect
    s = Recommender('w2v_limitingfactor_v1.model')
    s.connect_db()
    # import user data


    # prep user data
    good_list, bad_list, hist_list, val_list, ratings_dict = prep_data(
                        df, good_threshold=good_rate, bad_threshold=bad_rate)

    recs = pd.DataFrame(s.predict(good_list, bad_list, hist_list, val_list,
                        ratings_dict, n=100, harshness=1, scoring=False),
                        columns=['Title', 'Year', 'URL', 'Avg. Rating',
                        '# Votes', 'Similarity Score','Movie ID'])
    def links(x):
        '''Changes URLs to actual links'''
        return '<a href="%s">Go to the IMDb page</a>' % (x)
    recs['URL'] = recs['URL'].apply(links)
    recs['Vote Up'] = '<input type="checkbox" name="upvote" value=' + \
            recs['Movie ID'] + '>  Good idea<br>'
    recs['Vote Down'] = '<input type="checkbox" name="downvote" value=' \
        + recs['Movie ID'] + '>  Hard No<br>'
    id_list = recs['Movie ID'].to_list()
    recs = recs.drop(columns = 'Movie ID')

    session.clear()
    session['id_list'] = json.dumps(id_list)
    session['good_list'] = json.dumps(good_list)
    session['bad_list'] = json.dumps(bad_list)
    session['hist_list'] = json.dumps(hist_list)
    session['val_list'] = json.dumps(val_list)
    session['ratings_dict'] = json.dumps(ratings_dict)
    session['good_rate'] = good_rate
    session['bad_rate'] = bad_rate
    return render_template('public/Groa_recommendations.html',
                            data=recs.to_html(index=False,escape=False))

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

@application.route('/userlookup')
def userlookup():

    users = get_imdb_users()

    return render_template('public/user_search.html',users = users)

if __name__ == "__main__":
    application.run(port=5000, debug=True)
