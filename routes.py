from flask import Flask
from flask import render_template, redirect, make_response, request, url_for
# import logging as log
import json
import time
import pytz
import numpy as np
import os
import db_interact as db
import datetime

app = Flask(__name__, template_folder='templates')
app.debug = True



# log.basicConfig(filename='%s.log'%__name__, level=log.DEBUG, format='%(asctime)s: %(message)s', datefmt='%d-%b-%y %H:%M:%S')


class form():
    def call(self):
        if self.request.args.to_dict() == {}:
            return render_template(self.form, fields=self.empty)

        base = self.empty.copy()
        res_data = self.request.args.to_dict()
        # makse sure all keys in self.empty are included in base
        base.update(res_data)
        print("Data: %s" % base)

        if "" in [base[x] for x in base]:
            return render_template(self.form, error=("All fields must be filled." if self.error == None else self.error), fields=base)
        self.success = self.event(base)  # calls event funtion
        return render_template(self.form, success=("Success" if self.success == None else self.success), fields=self.empty)

    def __init__(self, request, empty, form, event=lambda x: "data processed but no event has been added", error=None, success=None):
        self.request = request
        self.empty = empty
        self.form = form
        self.event = event
        self.error = error
        self.success = success


@app.route("/submitform", methods=['POST'])
def submitform():
    print(request.form)
    return make_response(redirect(url_for('.%s'%request.form["id"])))



@app.route("/")
def home():
    return render_template("home.html")


@app.route('/home')
def home_redirect():
    return redirect("/", code=302)


@app.route('/add_student')
def add_student():
    return render_template("add_student_form.html", error = None, success=None)


@app.route('/add_teacher')
def add_teacher():
    empty = {"name_first": "", "name_last": "", "gender": "", "year_groups": "",
             "house": "", "dob": ""}
    f = form(request, empty, "add_teacher_form.html")
    return f.call()


@app.route('/add_event')
def add_event():
    empty = {"name": "", "time": "", "age_group": "",
             "track_feild": "", "timed_score_distance": "", "gender": ""}
    f = form(request, empty, "add_event_form.html", event=lambda x: x)
    return f.call()


@app.route('/cmd')
def cmd():
    try:
        a = eval(request.args.to_dict()["cmd"])
        return {"r": a}
    except Exception as e:
        return e


if __name__ == '__main__':
    app.run()
