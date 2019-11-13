# This file is part of Track In Time Server.
#
# Track In Time Server is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Track In Time Server is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Track In Time Server.  If not, see <https://www.gnu.org/licenses/>.

from flask import Flask
from flask import render_template, redirect, make_response, request, url_for
from werkzeug.exceptions import HTTPException

# import logging as log
import json
import time
import pytz
import numpy as np
import os
import secrets as s
try:
    import db_interact as db
except (ModuleNotFoundError, ImportError):
    print("Database import error")
import datetime

from forms import *

app = Flask(__name__, template_folder='templates')
app.config['SECRET_KEY'] = "".join([s.choice([chr(i) for i in range(32,127)]) for j in range(128)]) # gen random secret probs bad idea
app.debug = True

print("Secret key: %s" %app.config['SECRET_KEY'])

# log.basicConfig(filename='%s.log'%__name__, level=log.DEBUG, format='%(asctime)s: %(message)s', datefmt='%d-%b-%y %H:%M:%S')


@app.route("/")
def home():
    return render_template("home.html")


@app.route('/home')
def home_redirect():
    return redirect("/", code=302)

@app.route('/favicon.ico')
def favicon():
    return redirect("static/images/favicon.ico")


@app.route('/search', methods = ["GET","POST"])
def search():

    form = SearchUserForm()

    if form.validate_on_submit(): # sucess passing data do stuff
        return redirect('/home')

    return render_template("search.html", form=form)





@app.route('/add_student', methods = ["GET","POST"])
def add_student():
    form = AddStudentForm()
    if form.validate_on_submit(): # sucess passing data do stuff
        return redirect('/home')

    return render_template("input_template.html", form=form)


@app.route('/add_event', methods = ["GET","POST"])
def add_event():
    form = AddEvent()

    if form.validate_on_submit(): # sucess passing data do stuff
        return redirect('/home')

    return render_template("input_template.html", form=form)

@app.route("/user_info")
def user_info():
    return render_template("user_info.html")

@app.route("/event_info")
def event_info():
    return render_template("event_info.html")

@app.route("/license")
def license():
    return render_template("license.html")

@app.route('/cmd')
def cmd():
    try:
        a = eval(request.args.to_dict()["cmd"])
        return {"r": a}
    except Exception as e:
        return e


@app.errorhandler(HTTPException)
def error404(error):
    print(error, type(error))
    error = str(error)
    try:
        return(render_template("error.html", error_num=error.split(":",1)[0], error_txt=error.split(":",1)[1]))
    except IndexError:
        return(render_template("error.html", error_num="Infinity", error_txt="This error SHOULD in theory never be seen by the user."))

if __name__ == '__main__':
    app.run()
