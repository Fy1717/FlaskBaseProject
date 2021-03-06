#- * -coding: utf - 16 - * -

# -------------------------------------------- IMPORT AREA --------------------------------------------------------
from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
from flask_mysqldb import MySQL
from wtforms import Form, BooleanField, StringField, PasswordField, validators, TextAreaField
#from passlib.hash import sha256_crypt
from functools import wraps
import os
# -----------------------------------------------------------------------------------------------------------------


# ------------------------------------------  REGISTER FORM -------------------------------------------------------
class RegisterForm(Form):
    name = StringField("Name", validators=[validators.Length(min=4, max=30)])
    surname = StringField("Surname", validators=[validators.Length(min=4, max=30)])
    username = StringField("Username", validators=[validators.Length(min=4, max=30)])
    email = StringField("Email", validators=[validators.Email(message="Control it ")])
    password = PasswordField("Password", validators=[
        validators.DataRequired(message= "Enter a Password"),
        validators.EqualTo(fieldname= "confirm", message= "False Password")])
    confirm = PasswordField("Confirm Password")
# -----------------------------------------------------------------------------------------------------------------

# ------------------------------------------  LOGIN FORM -------------------------------------------------------
class LoginForm(Form):
    username = StringField("USERNAME")
    password = PasswordField("PASSWORD")
# -----------------------------------------------------------------------------------------------------------------

# ------------------------------------------ ARTICLE FORM -------------------------------------------------------
class ArticleForm(Form):
    title = StringField("TITLE", validators=[validators.Length(min=5, max=60)])
    content = TextAreaField("CONTENT", validators=[validators.Length(min=40)])
# -----------------------------------------------------------------------------------------------------------------

app = Flask(__name__)
app.secret_key = "hwblog"

# ------------------------------------------ MYSQL CONNECTION -----------------------------------------------------
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "hwblog"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"

mysql = MySQL(app)
# -----------------------------------------------------------------------------------------------------------------

# ------------------------------------------ PAGE ROUTES FUNCTIONS ------------------------------------------------

# MAIN ------------------
@app.route("/")
def index():
    return render_template("index.html")
# -----------------------

# LOGIN DECORATOR -------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Please Login", "danger")
            return redirect(url_for("login"))
    
    return decorated_function
#-----------------------------------------------------------------------------------------------------------------

# ABOUT -----------------
@app.route("/about")
def about():
    return render_template("about.html")
# -----------------------------------------------------------------------------------------------------------------

# REGISTER --------------
@app.route("/register", methods = ["GET", "POST"])
def register():
    form = RegisterForm(request.form)

    if request.method == "POST" and form.validate():
        name = form.name.data
        surname = form.surname.data
        username = form.username.data
        email = form.email.data
        password = form.password.data

        name = name + ' ' + surname

        cursor = mysql.connection.cursor()

        sorgu = "Insert into users(name, email, username, password) VALUES(%s, %s, %s, %s)"

        cursor.execute(sorgu,(name, email, username, password))

        mysql.connection.commit()

        cursor.close()

        flash("Successfully Register", "success")

        return redirect(url_for("login"))
    else:
        return render_template("register.html", form = form)
# -----------------------------------------------------------------------------------------------------------------

# LOGIN -----------------
@app.route("/login", methods = ["GET", "POST"])
def login():
    form = LoginForm(request.form)

    if request.method == "POST":
        username = form.username.data
        password = form.password.data

        cursor = mysql.connection.cursor()
        sorgu = "Select * From users where username = %s"

        result = cursor.execute(sorgu, (username,))

        if result > 0:
            data = cursor.fetchone()
            real_password = data["password"]

            if password == real_password:
                flash("Successfully Login..", "success")

                session["logged_in"] = True
                session["username"] = username
                
                return redirect(url_for("index"))
            else:
                flash("Please control user information..", "danger")

                return redirect(url_for("login"))

        else:
            flash("User not found..", "danger")

            return redirect(url_for("login"))


    return render_template("login.html", form = form)
# -----------------------------------------------------------------------------------------------------------------

# LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()

    return redirect(url_for("index"))
# -----------------------------------------------------------------------------------------------------------------

# DASHBOARD -------------
@app.route("/dashboard")
@login_required
def dashboard():
    cursor = mysql.connection.cursor()

    sorgu = "Select * from articles where author = %s"

    result = cursor.execute(sorgu, (session["username"],))

    if result > 0:
        articles = cursor.fetchall()

        return render_template("dashboard.html", articles = articles)
    else:
        return render_template("dashboard.html")

    return render_template("dashboard.html")
# -----------------------------------------------------------------------------------------------------------------

# PROFILE ------------
@app.route("/profile")
@login_required
def profile():
    cursor = mysql.connection.cursor()
    cursor2 = mysql.connection.cursor()
    sorgu = "Select * From users where username = %s"
    result = cursor.execute(sorgu, (session["username"],))

    if result > 0:
        # MEVCUT KULLANICI VE ID SI------
        user = cursor.fetchone()
        sorguUserId = "Select id from users where username= %s"
        resultUserId = cursor.execute(sorguUserId, (session["username"],))
        # -----------------------

        # MEVCUT KULLANICININ BAGLANTILARI ------
        sorguActiveConnections = "Select * from users where id in (Select user_from from connections as c where c.user_to = %s and c.status = 'approved') or id in (Select user_to from connections as c where c.user_from = %s and c.status = 'approved')"
        resultActiveConnectionsCount = cursor2.execute(sorguActiveConnections, (resultUserId, resultUserId))
        # -----------------------

        # MEVCUT KULLANICIYA GELEN BAGLANTI ISTEKLERI ------
        sorguForConnectionWaiting = "Select * from users where id in (Select user_from from connections as c where c.user_to = %s and c.status = %s)"
        resultWaiting = cursor.execute(sorguForConnectionWaiting, (resultUserId, 'waiting',))
        # -----------------------

        if resultWaiting > 0:
            requestedUsers = cursor.fetchall()

            if resultActiveConnectionsCount > 0:
                resultActiveConnections = cursor2.fetchall()
                
                return render_template("profile.html", user = user, requestedUsers = requestedUsers, requestedUsersCount = resultWaiting, resultActiveConnections = resultActiveConnections, resultActiveConnectionsCount = resultActiveConnectionsCount)
 
            return render_template("profile.html", user = user, requestedUsers = requestedUsers, requestedUsersCount = resultWaiting) 
        
        if resultActiveConnectionsCount > 0:
            resultActiveConnections = cursor2.fetchall()

            return render_template("profile.html", user = user, resultActiveConnections = resultActiveConnections, resultActiveConnectionsCount = resultActiveConnectionsCount)

        mysql.connection.commit()
        cursor.close()

        return render_template("profile.html", user = user)

    return render_template("profile.html")
# -----------------------------------------------------------------------------------------------------------------

# ARTICLE ----------------
@app.route("/article/<string:id>")
def article(id):
    cursor = mysql.connection.cursor()

    sorgu = "Select * from articles where id= %s"

    result = cursor.execute(sorgu, (id,))

    if result > 0:
        article = cursor.fetchone()

        return render_template("article.html", article = article)
    else:
        return render_template("article.html")

    return render_template("article.html")
# -----------------------------------------------------------------------------------------------------------------

# ARTICLES ----------------
@app.route("/articles")
def articles():
    cursor = mysql.connection.cursor()

    sorgu = "Select * from articles"

    result = cursor.execute(sorgu)

    if result > 0:
        articles = cursor.fetchall()

        return render_template("articles.html", articles = articles)
    else:
        return render_template("articles.html")

    return render_template("articles.html")
# -----------------------------------------------------------------------------------------------------------------

# ADD ARTICLE -----------
@app.route("/addarticle", methods = ["GET", "POST"])
def addarticle():
    form = ArticleForm(request.form)

    if request.method == "POST" and form.validate():
        title = form.title.data
        content = form.content.data

        cursor = mysql.connection.cursor()
        sorgu = "Insert into articles(title, author, content) VALUES(%s, %s, %s)"

        cursor.execute(sorgu, (title, session["username"], content))

        mysql.connection.commit()

        cursor.close()

        flash("Article is added successfully..", "success")

        return redirect(url_for("dashboard"))
    return render_template("addarticle.html", form=form)
# -----------------------------------------------------------------------------------------------------------------

# DELETE ARTICLE -----------
@app.route("/delete/<string:id>")
@login_required
def delete(id):
    cursor = mysql.connection.cursor()
    sorgu = "Select * from articles where author = %s and id = %s"
    result = cursor.execute(sorgu, (session["username"], id))

    if result > 0:
        sorgu2 = "Delete from articles where id = %s"

        cursor.execute(sorgu2, (id,))

        mysql.connection.commit()

        return redirect(url_for("dashboard"))
    else:
        flash("Article not found", "danger")

        return redirect(url_for("index"))
# -----------------------------------------------------------------------------------------------------------------

# UPDATE ARTICLE -----------
@app.route("/edit/<string:id>", methods = ["GET", "POST"])
def update(id):
    form = ArticleForm(request.form)

    if request.method == "GET":
        cursor = mysql.connection.cursor()
        sorgu = "Select * from articles where id= %s and author = %s"

        result = cursor.execute(sorgu, (id, session["username"]))

        if result == 0:
            flash("DANGER!", "danger")
            return redirect(url_for("index"))
        else:
            article = cursor.fetchone()
            form = ArticleForm()

            form.title.data = article["title"]
            form.content.data = article["content"]

            return render_template("update.html", form=form)
    else:
        form = ArticleForm(request.form)
        newTitle = form.title.data
        newContent = form.content.data

        sorgu2 = "Update articles Set title = %s, content = %s where id = %s"
        cursor = mysql.connection.cursor()

        cursor.execute(sorgu2, (newTitle, newContent, id))

        mysql.connection.commit()

        flash("Article has been updated successfully", "success")
    return redirect(url_for("dashboard"))
# -----------------------------------------------------------------------------------------------------------------

# SEARCH INSTRUCTOR -----------
@app.route("/searchInstructor", methods = ["GET", "POST"])
def searchInstructor():
    if request.method == "GET":
        return redirect(url_for("index"))
    else:
        keyword = request.form.get("keyword")

        cursor = mysql.connection.cursor()

        sorgu = "Select * from users where name like '%" + keyword + "%'"

        result = cursor.execute(sorgu)

        if result == 0:
            flash("Instructor is not found...", "danger")

            return redirect(url_for("instructors"))
        else: 
            flash("Successful...", "success")

            instructors = cursor.fetchall()

            return render_template("instructors.html", instructors = instructors)
# -----------------------------------------------------------------------------------------------------------------

# SEARCH ARTICLE -----------
@app.route("/search", methods = ["GET", "POST"])
def search():
    if request.method == "GET":
        return redirect(url_for("index"))
    else:
        keyword = request.form.get("keyword")

        cursor = mysql.connection.cursor()

        sorgu = "Select * from articles where title like '%" + keyword + "%'"

        result = cursor.execute(sorgu)

        if result == 0:
            flash("Article is not found...", "danger")

            return redirect(url_for("articles"))
        else: 
            flash("Successful...", "success")

            articles = cursor.fetchall()

            return render_template("articles.html", articles = articles)
# -----------------------------------------------------------------------------------------------------------------

# INSTRUCTORS ------------
@app.route("/instructors")
def instructors():
    cursor = mysql.connection.cursor()

    sorgu = "Select * from users"

    result = cursor.execute(sorgu)

    if result > 0:
        instructors = cursor.fetchall()

        return render_template("instructors.html", instructors = instructors)
    else:
        return render_template("instructors.html")

    return render_template("instructors.html")
# -----------------------------------------------------------------------------------------------------------------

# INSTRUCTOR -----------
@app.route("/instructor/<string:id>")
def instructor(id):
    cursor = mysql.connection.cursor()
    cursor1 = mysql.connection.cursor()
    cursor2 = mysql.connection.cursor()

    sorgu = "Select * From users where id = %s"
    sorguUserId = "Select id from users where username= %s"
    sorgu2 = "Select status from connections where user_from= %s and user_to= %s"

    resultSessionUser = cursor.execute(sorguUserId, (session["username"],))

    if resultSessionUser > 0:
        # MEVCUT KULLANICI VE ID SI------
        user = cursor.fetchone()
        resultSessionUserId = cursor.execute(sorguUserId, (session["username"],))
        # -----------------------

        if int(resultSessionUserId) == int(id):
            return redirect(url_for("profile"))
        else:
            result = cursor1.execute(sorgu, (id,))

            if result > 0:  
                instructor = cursor1.fetchone()
                resultStatus = cursor2.execute(sorgu2, (id, resultSessionUserId))

                if resultStatus > 0:
                    status = cursor2.fetchone()

                    return render_template("instructor.html", instructor = instructor, status = status)
                else:
                    return render_template("instructor.html", instructor = instructor)
            else:
                return render_template("instructor.html")

    return render_template("instructor.html")
# -----------------------------------------------------------------------------------------------------------------

# SEND FRIENDSHIP CONNECTION REQUEST -----------
@app.route("/connection/request/<string:id>", methods = ["GET", "POST"])
@login_required
def sendConnectionRequest(id):
    cursor = mysql.connection.cursor()
    sorgu = "Select * From users where username = %s"
    result = cursor.execute(sorgu, (session["username"],))

    if result > 0:
        # MEVCUT KULLANICI VE ID SI------
        user = cursor.fetchone()
        sorguUserId = "Select id from users where username= %s"
        resultUserId = cursor.execute(sorguUserId, (session["username"],))
        # -----------------------

        cursor1 = mysql.connection.cursor()
        sorgu1 = "Select * from connections where user_from= %s and user_to= %s"
        cursor1.execute(sorgu1, (resultUserId, id))
        result = cursor1.execute(sorgu1, (id,))

        if result > 0:
            sorgu2 = "Update connections Set status= %s where user_from= %s and user_to= %s"
            cursor1.execute(sorgu2, ('waiting', resultUserId, id))

            flash("Request is sent successfully..", "success")
        else:
            sorgu2 = "Insert into connections(user_from, user_to, status) VALUES(%s, %s, %s)"
            cursor.execute(sorgu2, (resultUserId, id, 'waiting'))

        mysql.connection.commit()
        cursor.close()

        flash("Request is sent successfully..", "success")

    return render_template("instructor.html")

# -----------------------------------------------------------------------------------------------------------------

# ACCEPT FRIENDSHIP REQUEST -----------
@app.route("/profile/accept/<string:id>", methods = ["GET", "POST"])
@login_required
def acceptFriendShip(id):
    cursor = mysql.connection.cursor()
    cursor1 = mysql.connection.cursor()
    sorgu = "Select * From users where username = %s"
    result = cursor.execute(sorgu, (session["username"],))

    if result > 0:
        # MEVCUT KULLANICI VE ID SI------
        user = cursor.fetchone()
        sorguUserId = "Select id from users where username= %s"
        resultUserId = cursor.execute(sorguUserId, (session["username"],))
        # -----------------------

        sorgu1 = "Select * from connections where user_from= %s and user_to= %s and status= 'waiting'"
        result1 = cursor1.execute(sorgu1, (id, resultUserId))

        if result1 > 0:
            sorgu2 = "Update connections Set status= %s where user_from= %s and user_to= %s and status= 'waiting'"
            cursor.execute(sorgu2, ('approved', id, resultUserId))

            flash("Request is accepted successfully..", "success")

        mysql.connection.commit()
        cursor.close()

    return redirect(url_for("profile"))
# -----------------------------------------------------------------------------------------------------------------

# REJECT FRIENDSHIP REQUEST -----------
@app.route("/profile/reject/<string:id>", methods = ["GET", "POST"])
@login_required
def rejectFriendShip(id):
    cursor = mysql.connection.cursor()
    cursor1 = mysql.connection.cursor()
    sorgu = "Select * From users where username = %s"
    result = cursor.execute(sorgu, (session["username"],))

    if result > 0:
        # MEVCUT KULLANICI VE ID SI------
        user = cursor.fetchone()
        sorguUserId = "Select id from users where username= %s"
        resultUserId = cursor.execute(sorguUserId, (session["username"],))
        # -----------------------

        sorgu1 = "Select * from connections where user_from= %s and user_to= %s and status= 'waiting'"
        result1 = cursor1.execute(sorgu1, (id, resultUserId))

        if result1 > 0:
            sorgu2 = "Update connections Set status= %s where user_from= %s and user_to= %s and status= 'waiting'"
            cursor.execute(sorgu2, ('rejected', id, resultUserId))

            flash("Request is rejected successfully..", "danger")

        mysql.connection.commit()
        cursor.close()

    return redirect(url_for("profile"))
# -----------------------------------------------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(debug = True)