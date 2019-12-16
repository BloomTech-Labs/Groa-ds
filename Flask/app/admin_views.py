from app import app

from flask import render_template

@app.route("/admin/dashboard")
def index():
	return render_template("admin/dashboard.html")

@app.route("/admin/profile")
def about():
    return "admin profile"