#!/usr/local/bin/python

#- * -coding: utf - 16 - * -

from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt

app = Flask(__name__)

@app.route("/")
def index():
    educations = ["Flutter", "Python", "Xamarin", "Javascript", "Firebase"]

    instructors = [{
        "id": 1,
        "name": "Furkan YILDIZ",
        "profession": "PYTHON"
    }, {
        "id": 2,
        "name": "Kadriye MACIT",
        "profession": "FLUTTER"
    }, {
        "id": 3,
        "name": "Beyza INCE",
        "profession": "ARTIFICAL INTELLIGENCE"
    }, {
        "id": 4,
        "name": "Oguz DEMIR",
        "profession": "JAVASCRIPT"
    }, {
        "id": 5,
        "name": "Alp YURTSEVEN",
        "profession": "ASP .NET"
    }]

    return render_template("index.html", instructors=instructors, educations=educations)

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/instructors/<string:id>")
def detail(id):
    return "Instructor " + id 

if __name__ == "__main__":
    app.run(debug = True)