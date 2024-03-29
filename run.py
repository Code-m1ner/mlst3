import os
from flask import (
    Flask, flash, render_template,
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
import json
from werkzeug.security import generate_password_hash, check_password_hash

if os.path.exists("env.py"):
    exec(open("env.py").read())
    import env

app = Flask(__name__)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")

# app.config["MONGO_DBNAME"]=env.MONGO_DBNAME
# app.secret_key = env.SECRET_KEY
# app.config["MONGO_URI"] = env.MONGO_URI
mongo = PyMongo(app)



@app.route("/")
#   Loads all the created cusines by users on the home page
@app.route("/get_cusine")
def get_cusine():
    with open("data/cusine.json", "r") as json_data:
        data = json.load(json_data)
    return render_template("cusines.html", cusine=data)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # check if username already exists in db
        existing_user = mongo.db.user.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            flash("Username already exists")
            return redirect(url_for("register"))

        register = {
            "username": request.form.get("username").lower(),
            "password": generate_password_hash(
                request.form.get("password"))
        }
        mongo.db.user.insert_one(register)

        # put the new user into 'session' cookie
        session["user"] = request.form.get("username").lower()
        flash("Registration Successful!")
        return redirect(url_for(
            "profile", username=session["user"]))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # check if username exists in db
        existing_user = mongo.db.user.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            # ensure hashed password matches user input
            if check_password_hash(
                    existing_user["password"], request.form.get("password")):
                session["user"] = request.form.get(
                    "username").lower()
                flash("Welcome, {}".format(
                    request.form.get("username")))
                return redirect(url_for(
                    "profile", username=session["user"]))
            else:
                # invalid password match
                flash("Incorrect Username and/or Password")
                return redirect(url_for("login"))

        else:
            '''username doesn't exist'''
            flash("Incorrect Username and/or Password")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/profile/<username>", methods=["GET", "POST"])
def profile(username):
    # grab the session user's username from db
    username = mongo.db.user.find_one(
        {"username": session["user"]})["username"]
    # This loads recipe to the users profile
    cusines = mongo.db.cusines.find()
    return render_template("profile.html", username=username, cusines=cusines)


@app.route("/logout")
def logout():
    # remove user from session cookie
    flash("You have been logged out")
    session.pop("user")
    return redirect(url_for("login"))


@app.route("/add_cusine", methods=["GET", "POST"])
def add_cusine():
    # Add recipe
    if request.method == "POST":
        cusines = {
            "category_name": request.form.get("category_name"),
            "recipe_name": request.form.get("recipe_name"),
            "recipe_preparation": request.form.get("recipe_preparation"),
            "recipe_ingredients": request.form.get("recipe_ingredients"),
            "recipe_calories": request.form.get("recipe_calories"),
            "created_by": session["user"]
        }
        mongo.db.cusines.insert_one(cusines)
        flash("Cusine successfully Added")
        # redirects user to the profile
        return redirect(url_for('profile', username=session['user']))

    categories = mongo.db.categories.find().sort("category_name", 1)
    return render_template("add_cusine.html", categories=categories)


@app.route("/edit_cusine/<cusine_id>", methods=["GET", "POST"])
def edit_cusine(cusine_id):
    # edits cusine/recipe
    if request.method == "POST":
        submit = {
            "category_name": request.form.get("category_name"),
            "recipe_name": request.form.get("recipe_name"),
            "recipe_preparation": request.form.get("recipe_preparation"),
            "recipe_ingredients": request.form.get("recipe_ingredients"),
            "recipe_calories": request.form.get("recipe_calories"),
            "created_by": session["user"]
        }
        mongo.db.cusines.update({"_id": ObjectId(cusine_id)}, submit)
        flash("Cusine successfully Updated")
        # redirects user to profile
        return redirect(url_for('profile', username=session['user']))
    cusine = mongo.db.cusines.find_one({"_id": ObjectId(cusine_id)})
    categories = mongo.db.categories.find().sort("category_name", 1)
    return render_template(
        "edit_cusine.html", cusine=cusine, categories=categories)


@app.route("/delete_cusine/<cusine_id>")
def delete_cusine(cusine_id):
    # deletes the cusine
    mongo.db.cusines.remove({"_id": ObjectId(cusine_id)})
    flash("Cusine successfully Deleted")
    return redirect(url_for('profile', username=session['user']))


@app.route("/get_categories")
def get_categories():
    # gets the categories from the database
    categories = list(mongo.db.categories.find().sort("category_name", 1))
    return render_template("categories.html", categories=categories)


@app.route("/add_category", methods=["GET", "POST"])
def add_category():
    # adding new category
    if request.method == "POST":
        category = {
            "category_name": request.form.get("category_name")
        }
        mongo.db.categories.insert_one(category)
        flash("New Category Added")
        return redirect(url_for("get_categories"))

    return render_template("add_category.html")


@app.route("/edit_category/<category_id>", methods=["GET", "POST"])
def edit_category(category_id):
    # edit category
    if request.method == "POST":
        submit = {
            "category_name": request.form.get("category_name")
        }
        mongo.db.categories.update({"_id": ObjectId(category_id)}, submit)
        flash("Category Successfully Updated")
        return redirect(url_for("get_categories"))

    category = mongo.db.categories.find_one({"_id": ObjectId(category_id)})
    return render_template("edit_category.html", category=category)


@app.route("/delete_category/<category_id>")
def delete_category(category_id):
    # detes category selected
    mongo.db.categories.remove({"_id": ObjectId(category_id)})
    flash("Category Successfully Deleted")
    return redirect(url_for("get_categories"))


# The following functions loads data from the json
#  imported on the top to render sample html
@app.route("/pasta")
def pasta():
    with open("data/cusine.json", "r") as json_data:
        data = json.load(json_data)
    return render_template("pasta.html", page_title="Pasta", cusine=data)


# This render's an html file with
# a click on the home button labelled accordingly
@app.route("/beef")
def beef():
    with open("data/cusine.json", "r") as json_data:
        data = json.load(json_data)
    return render_template("beef.html", page_title="beef", cusine=data)


# if __name__ == "__main__":
#     app.run(host=os.environ.get(
#         "IP"), port=int(
#             os.environ.get(
#                 "PORT")), debug=False)
if __name__ == '__main__':
    host = os.environ.get("IP", "0.0.0.0")  # Default host is '0.0.0.0'
    port = int(os.environ.get("PORT", 5000))  # Default port is 5000
    app.run(host=host, port=port, debug=False)