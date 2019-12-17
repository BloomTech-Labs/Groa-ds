from app import app
import pandas as pd
from flask import render_template, request, redirect

import os

@app.route("/")
def index():
	return render_template("public/index.html")

@app.route("/jinja")
def jinja():

    my_name = "Jeff"

    return render_template("public/jinja.html", my_name=my_name)

@app.route("/about")
def about():
    return "<h1 style='color: red'> About!</h1>"

#app.config["FILE_UPLOADS"] = r"d:\code\repos\Groa\Flask\app\static\uploads"

@app.route("/upload", methods=["GET", "POST"])
def upload():

    if request.method == "POST":
        if request.files:

            file = request.files["file"]
            df = pd.read_csv(file)
            #file.save(os.path.join(app.config["FILE_UPLOADS"], file.filename))

            #print("File saved")

            return redirect(request.url)


    return render_template("public/upload.html")
