from flask import Flask, session, render_template, request, flash, redirect, send_file
from flask_session import Session
from time import sleep
import pandas as pd
import math
import numpy as np
from zipfile import ZipFile
import json
import os, shutil, io
import psycopg2

# self import
from psycopg2_blob import *
from w2v_inference import *
from r2v_inference import *
from functions import *

application = Flask(__name__)
application.secret_key = 'secret_bee'
SESSION_TYPE = 'filesystem'
application.config.from_object(__name__)
Session(application)

# paths to the recommender models
master_w2v = 'models/w2v_limitingfactor_v3.51.model'
master_r2v = 'models/r2v_Botanist_v1.1000.5.model'

@application.route("/")
def index():
    '''
    Main Page, has no real function as of now
    '''
    return render_template("public/Homepage.html")

@application.route("/letterboxd_upload", methods=["GET", "POST"])
def lb_upload():
    '''
    Allows you to upload your ratings CSV that you got from IMDb
    '''
    return render_template('public/letterboxd_upload.html')

@application.route('/imdb_upload')
def imdb_upload():
    '''
    allows you to upload your ratings csv that you got from imdb
    '''
    return render_template('public/imdb_upload.html')

@application.route('/letterboxd_submission', methods=['GET','POST'])
def lb_submit():
    '''
    Next step for letterboxd. This page gets the zipfile from the previous page,
    extracts 4 CSVs and commits them to the session. The HTML page presents
    2 sliders and 3 checkboxers that are used by the model
    '''
    # ensure POST request
    if request.method != "POST":
        return redirect(request.url)

    # ensure POST request has the file part
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)

    # ensure file name
    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)

    # set source of user data to previous route name
    site = str(request.referrer).rsplit("/")[-1]

    session.clear() # clear any leftovers from previous recommendations
    file = request.files["file"]
    tag = str(np.random.uniform()) # make a temp folder with a random name
    with ZipFile(file, 'r') as zip:
        zip.extractall(path=f'temp{tag}', members=['ratings.csv',
                                                   'reviews.csv',
                                                   'watchlist.csv',
                                                   'watched.csv'])

    # letterboxd seems to always export as cp1252 encoding regardless of users' OS. Weird!
    ratings = pd.read_csv(f'temp{tag}/ratings.csv', encoding='cp1252')
    reviews, watched, watchlist = multi_read(['reviews','watched','watchlist'],tag)

    # save user data to session.
    (session['ratings'],
    session['reviews'],
    session['watched'],
    session['watchlist']) = multi_jsonify([ratings,reviews,watched,watchlist])

    sleep(1) # wait for session to save (prevents race condition while session saves)
    shutil.rmtree(f'temp{tag}') # remove temp folder if exists

    return render_template('public/user_submission.html',
                            data=ratings.sort_values(by=['Date'],
                            ascending=False).head().to_html(index=False),
                            site=site)

@application.route('/imdb_submission',methods = ['GET','POST'])
def imdb_submit():
    '''
    the result of the imdb upload, you can see a table of your rated movies
    and adjust them according to year released and personal rating
    '''
    # ensure POST request
    if request.method != "POST":
        return redirect(request.url)

    # check if the post request has the file part
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)

    # no file name
    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)

    # set source of user data to previous route name
    site = str(request.referrer).rsplit("/")[-1]

    session.clear() # clear any leftovers from previous recommendations
    try:
        ratings = pd.read_csv(file, encoding='cp1252')
    except:
        ratings = pd.read_csv(file, encoding='latin1')

    # strip leading "tt"s from ID column
    ratings['Const'] = ratings['Const'].str.strip('t')
    ratings = ratings.drop(columns=['Title Type','Num Votes','Directors','Genres',
                            'URL','Release Date', 'Const'], errors='ignore')
    session['ratings'] = ratings.to_json()

    return render_template('public/user_submission.html',
            name='Watched List', data=ratings.sort_values(by=['Date Rated'],
            ascending=False).head().to_html(index=False), site=site)

@application.route('/groa_recommendations', methods=['GET', 'POST'])
def groa_recommend():
    '''
    Shows recommendations given user data and selected options.
    Referring page is used to infer which data are present, and thus
    which options are available.
    '''
    if '/user_reviews' in str(request.referrer):
        reviews = pd.read_json(session['reviews'])
    if ('/imdb_submission' or '/user_reviews') in str(request.referrer):
        bad_rate = int(request.form['bad_rate'])/2 # convert IMDb slider input to 5-point scale
        good_rate = int(request.form['good_rate'])/2
        watched = pd.DataFrame() # IMDb user only uploads ratings
        watchlist = pd.DataFrame()
    if '/letterboxd_submission' in str(request.referrer):
        (reviews,
        watched,
        watchlist) = multi_read_json(['reviews','watched','watchlist'])
        bad_rate = float(request.form['bad_rate']) # slider input
        good_rate = float(request.form['good_rate']) # slider input
    ratings = pd.read_json(session['ratings'])
    hidden = "hidden" in request.form # user requests hidden gems
    cult = "cult" in request.form # user requests cult movies
    extra_weight = "extra_weight" in request.form # user requests extra weighting

    # initialize both models and connect them to database
    s = Recommender(master_w2v)
    s.connect_db()
    r = r2v_Recommender(master_r2v)
    r.connect_db()

    # prep user watch history
    good_list, bad_list, hist_list, val_list, ratings_dict = prep_data(
                                        ratings, watched, watchlist,
                                        good_threshold=good_rate,
                                        bad_threshold=bad_rate)

    # pass dictionary of ratings if the user requests extra weighting
    weighting = ratings_dict if extra_weight else {}

    # get recs based on ratings, watch history
    recs = pd.DataFrame(s.predict(good_list, bad_list, hist_list, val_list,
                        ratings_dict=weighting),
                        columns=['Title', 'Year', 'URL', 'Avg. Rating',
                        '# Votes', 'Similarity Score','Movie ID'])

    # make empty dataframes to return in case hidden or cult is deselected
    hidden_df = cult_df = pd.DataFrame()

    if hidden or cult:
        reviews = prep_reviews(reviews) # prep user reviews
        cult_results, hidden_results = r.predict(reviews, hist_list=hist_list)
        optional_cols = ['Title', 'Year', 'URL', '# Votes', 'Avg. Rating',
                                'User Rating', 'Reviewer', 'Review', 'Movie ID']
        if cult:
            cult_df = pd.DataFrame(cult_results, columns=optional_cols)
            cult_df = rec_edit(cult_df, val_list) # Applies inline HTML formatting
        if hidden:
            hidden_df = pd.DataFrame(hidden_results, columns=optional_cols)
            hidden_df = rec_edit(hidden_df, val_list) # Applies inline HTML formatting

    # Make column to show most similar movie from the user's good_list
    # This runs 10x faster if not in a function. Probably a threading thing.
    recs['Liked by fans of...'] = recs['Movie ID'].apply(lambda x: s.get_most_similar_title(x, good_list))
    recs = rec_edit(recs, val_list) # Applies inline HTML formatting

    # Save dataframes for exporting to CSV later
    session['hidden_df'] = hidden_df.to_json()
    session['cult_df'] = cult_df.to_json()
    session['recs'] = recs.to_json()

    (session['id_list'], # save variables that we use for repeat inferencing
    session['good_list'],
    session['bad_list'],
    session['hist_list'],
    session['val_list'],
    session['ratings_dict'],
    session['checked_list'], # initialize empty 'checked' and 'rejected' lists for later
    session['rejected_list']) = multi_dump([recs['Movie ID'].to_list(), good_list,
                                bad_list, hist_list, val_list, ratings_dict, [], []])
    (session['good_rate'],
    session['bad_rate'],
    session['extra_weight']) = multi_session([good_rate,bad_rate,extra_weight])

    recs = recs.drop(columns='Movie ID')

    return render_template('public/Groa_recommendations.html',
                            data = recs.to_html(index=False,escape=False),
                            hidden_data = hidden_df.to_html(index=False,escape=False),
                            cult_data = cult_df.to_html(index=False,escape=False))

@application.route('/resubmission',methods=['POST'])
def resubmit():
    '''
    This page adds approved and rejected movies to checked_list and rejected_list
    respectively and uses them for an improved set of recommendations.
    '''

    checked_list = json.loads(session['checked_list'])
    rejected_list = json.loads(session['rejected_list'])
    checked_list.extend(request.form.getlist('upvote')) # store upvotes
    rejected_list.extend(request.form.getlist('downvote')) # store downvotes

    (id_list,
    good_list,
    bad_list,
    hist_list,
    val_list,
    ratings_dict) = multi_load(['id_list','good_list','bad_list',
                                'hist_list','val_list', 'ratings_dict'])

    s = Recommender(master_w2v)
    s.connect_db()

    # pass dictionary of ratings if the user requests extra weighting
    weighting = ratings_dict if session['extra_weight'] else {}

    stride = len(checked_list) + len(rejected_list) # number of recs to replace

    recs = pd.DataFrame(s.predict(good_list, bad_list, hist_list, val_list,
                ratings_dict=weighting, checked_list=checked_list,
                rejected_list=rejected_list,
                n=100+stride, harshness=1, scoring=False),
                columns=['Title', 'Year', 'URL', 'Avg. Rating', '# Votes',
                'Similarity Score','Movie ID'])

    recs['Liked by fans of...'] = recs['Movie ID'].apply(lambda x: s.get_most_similar_title(x, good_list))

    recs = rec_edit(recs, val_list) # apply HTML formatting to recs

    # update full recs list preserving ordering
    id_list2 = [x for x in recs['Movie ID'].to_list() if x not in id_list]
    id_list.extend(id_list2)
    # color-code columns
    recs['New Rec?'] = bool_func(recs['Movie ID'], id_list2)
    recs['Title'] = highlight_watchlist(recs['Movie ID'], recs['Title'], val_list)
    recs = recs[cols[-1:] + recs.columns.to_list()[:-1]] # moves New Rec? column to first column

    # Save recs and user feedback for later
    session['recs'] = recs.to_json()
    (session['id_list'],
    session['checked_list'],
    session['rejected_list']) = multi_dump([id_list2, checked_list, rejected_list])

    return render_template('public/re_recommendations.html',
                            data=recs.drop(columns='Movie ID')
                            .to_html(escape=False,index=False))

@application.route('/export_recs', methods=['POST'])
def download_recs():
    """Creates a download popup for one of 4 possible dataframes"""
    tag = str(np.random.uniform())[2:7] # random tag for temp filename
    os.makedirs('exports', exist_ok=True) # make /exports if it doesn't exist yet
    if "upvote" in request.form['button']: # export user upvotes only
        my_path = f'exports/Groa_upvotes{tag}.csv'
        checked_list = json.loads(session['checked_list'])
        checked_list.extend(request.form.getlist('upvote')) # get recent upvotes
        s = Recommender(master_w2v)
        s.connect_db()
        checked_list = [fill_id(x) for x in checked_list]
        checked_info = [s._get_info(x) for x in checked_list]
        recs_df = pd.DataFrame(checked_info,
                                columns=['Title', 'Year', 'URL',
                                'Avg. Rating', '# Votes','Blank', 'ID'])
        # drop ID because Excel truncates numbers with leading zeroes
        recs_df = recs_df.drop(columns=['Blank', 'ID'])
    elif "cult" in request.form['button']: # export cult movie recs only
        my_path = f'exports/Groa_cult_movies{tag}.csv'
        recs_df = pd.read_json(session['cult_df'])
    elif "hidden" in request.form['button']: # export hidden gem recs only
        my_path = f'exports/Groa_hidden_gems{tag}.csv'
        recs_df = pd.read_json(session['hidden_df'])
    else: # export all recs
        my_path = f'exports/Groa_recs{tag}.csv'
        recs_df = pd.read_json(session['recs'])
        recs_df = recs_df.drop(columns=['Vote Up', 'Vote Down'])
    recs_df.to_csv(my_path, index=False)
    return_data = io.BytesIO() # write file to memory so it can be deleted
    with open(my_path, 'rb') as myfile:
        return_data.write(myfile.read())
    return_data.seek(0) # move cursor to start
    os.remove(my_path) # delete temp directory
    return send_file(return_data, mimetype='text/csv')

@application.route('/user_search',methods = ["GET","POST"])
def user_search():
    users = read_users("Usernames.txt") # get all (ascii) usernames
    return render_template('public/user_search.html', users=users)

@application.route('/user_reviews',methods = ["GET","POST"])
def user_reviews():
    name = request.form['Username']
    df, ratings, reviews = imdb_user_lookup(name)
    session['ratings'], session['reviews'] = multi_jsonify([ratings, reviews])
    return render_template('public/user_reviews.html',
                            data=df.head(10).to_html(index=False), name=name)

if __name__ == "__main__":
    application.run(port=5000)
