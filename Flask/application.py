from flask import Flask, render_template, request, flash, redirect
import pandas as pd
#from zipfile import ZipFile

import psycopg2
#from getpass import getpass

#self import
from psycopg2_blob import query,query2,query3
from model_functions import ScoringService


application = Flask(__name__)

@application.route("/")
def index():
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

@application.route('/imdb_upload', methods=['GET', 'POST'])
def imdb_upload():
    if request.method == 'GET':
        return render_template('public/imdb_upload.html')

    elif request.method == 'POST':
        username = request.form['username']

        #search database for user
        reviewsandratings = query(username)
        #shows reviews and ratings as a list
        #what if username isn't there? scrape it from imdb?


        return render_template('public/imdb_upload_result.html')
        

@application.route('/recommendations', methods=['GET', 'POST'])
def recommend():
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
        

if __name__ == "__main__":
    application.run(port=5000, debug=True)