import os
import datetime
from flask import (
    Flask, flash, render_template,
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
if os.path.exists("env.py"):
    import env


app = Flask(__name__)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")
app.register_key = os.environ.get("REGISTER_KEY")
mongo = PyMongo(app)


@app.route("/")
@app.route("/login", methods=["GET", "POST"])
def login():
    """Log the user in.

    On Get renders the login page.
    On Post verifies the user's password and if valid
    sets the user as the sesson user
    and renders the User Base page.

    :return: user_home.html
    :rtype: n/a
    """

    if request.method == "POST":
        # check db for matching username
        old_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if old_user:
            # use Wertzeug to check stored password matches user input
            if check_password_hash(old_user["password"], request.form.get(
                    "password")):
                # set user as sesson user
                session["user"] = request.form.get("username").lower()
                # render User Base page
                return redirect(url_for(
                    "user_home", username=session["user"]))
            else:
                # invalid password match
                flash("Entry Incorrect")
                # render Login page
                return redirect(url_for("login"))

        else:
            # username doesn't exist
            flash("Entry Incorrect")
            # render Login page
            return redirect(url_for("login"))

    # render Login page
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register the user.

    On Get renders the Register page.
    On Post verifies the imput key and if valid
    sets the user as the sesson user,
    creates a MongoDB document with their details
    and renders the User Base page.

    :return: user_home.html
    :rtype: n/a
    """

    if request.method == "POST":
        if request.form.get("key").lower() == app.register_key:

            # check Mongo to see if username is taken
            old_user = mongo.db.users.find_one(
                {"username": request.form.get("username").lower()})

            if old_user:
                flash("Username taken try again")
                return redirect(url_for("register"))

            # create new user dictionary
            new_user = {
                "username": request.form.get("username").lower(),
                "firstname": request.form.get("firstname").lower(),
                "lastname": request.form.get("lastname").lower(),
                "job_title": request.form.get("job_title").title(),
                "password": generate_password_hash(
                    request.form.get("password"))
            }
            # insert new user document into Mongo
            mongo.db.users.insert_one(new_user)

            # set session cookie to this username
            session["user"] = request.form.get("username").lower()
            flash("Welcome aboard, {}".format(
                            request.form.get("username")))
            # render User Base page
            return redirect(url_for("user_home", username=session["user"]))
        else:
            flash("Invalid Key")
    # render Register page
    return render_template("register.html")


@app.route("/user_home/<username>")
def user_home(username):
    """Render the User Base page.

    Renders the User Base page setting the value
    in the header box to the passed username parameter,
    getting the department's name values from Mongo
    along with the script and shot list data.

    :param username: the user's username
    :type username: str
    :return: user_home.html
    :rtype: n/a
    """

    if session["user"]:
        # get depts, latest_script, shotlist and users
        # collections data from Mongo
        script = list(mongo.db.latest_script.find())
        depts = list(mongo.db.depts.find())
        shotlist = list(mongo.db.shotlist.find())
        username = mongo.db.users.find_one(
            {"username": session["user"]})["username"]
        # render the User Base page
        return render_template(
            "user_home.html", username=username,
            script=script, shotlist=shotlist, depts=depts)


@app.route("/get_depts")
def get_depts():
    """Renders the Departments page.

    Renders the Departments page getting the name
    values from Mongo.

    :return: Departments.html
    :rtype: n/a
    """

    if session["user"]:
        # get depts collection's data from Mongo
        depts = mongo.db.depts.find()
        # render the Departments page
        return render_template("depts.html", depts=depts)


@app.route("/get_pro")
def get_pro():
    """Renders the Production latest messages template page.

    Renders the Production Latest Messages page with the latest
    messages showing for the Production department
    getting the department's messages from Mongo.

    :return: pro.html
    :rtype: n/a
    """

    if session["user"]:
        # get production collection's latest documents from Mongo
        depart = list(mongo.db.production.find().sort('date', -1).limit(10))

        # render the Production Latest messages page
        return render_template(
            "pro.html", dep="Latest Production Updates", depart=depart)


@app.route("/get_dep/<dep>", methods=["GET", "POST"])
def get_dep(dep):
    """Renders the Department Messages by Date page.

    On Get renders the Department Messages by Date page with that day's
    messages showing for each department
    depending on which department name is passed as a parameter
    getting that department's messages from Mongo.
    On Post renders the Department messages page for each department
    depending on which department name is passed as a parameter
    getting that department's messages from Mongo
    for whichever date value is supplied.

    :param dep: the department selected by the user
    :type dep: str
    :return: dep.html
    :rtype: n/a
    """

    if session["user"]:
        dep = dep
        day = datetime.datetime.now()
        today = day.strftime("%d %B, %Y")
        # get selected department collection's documents posted
        # today from Mongo
        depart = list(mongo.db[dep].find({"date": today}))
        if request.method == "POST":
            date = request.form.get("date")
            # get selected department collection's documents
            # with this date from Mongo
            depart = list(mongo.db[dep].find(
                {"date": date}))

            # render the selected Department page
            return render_template(
                "dep.html", dep=dep, depart=depart, date=date, day=date)
        # render the selected Department page
        return render_template(
            "dep.html", dep=dep, depart=depart, date=today, day="TODAY")


@app.route("/get_poster/<dep>", methods=["GET", "POST"])
def get_poster(dep):
    """Renders the Department Messages by Poster page.

    On Get renders the Department Messages by Poster page with the latest
    messages showing for each department
    depending on which department name is passed as a parameter
    getting that department's messages from Mongo.
    On Post renders the Department messages page for each department
    depending on which department name is passed as a parameter
    getting that department's messages from Mongo
    for whichever poster value is supplied.

    :param dep: the department selected by the user
    :type dep: str
    :return: dep_poster.html
    :rtype: n/a
    """

    if session["user"]:
        # get selected department collection's last 10 documents from Mongo
        depart = list(mongo.db[dep].find().sort('date', -1).limit(10))
        dep = dep
        if request.method == "POST":
            poster = request.form.get("poster").lower()
            # get selected department collection's documents by this
            # poster from Mongo
            depart = list(mongo.db[dep].find(
                {"poster": poster}))

            # render the Department page
            return render_template(
                "dep-poster.html", dep=dep, depart=depart, day=poster)
        # render the Department page
        return render_template(
            "dep-poster.html", dep=dep, depart=depart, day="Latest")


@app.route("/get_all/<dep>")
def get_all(dep):
    """Render the Department by Date page with all messages
    for choosen department.

    Renders the Department page with all messages for the choosen department
    getting that department's messages from Mongo.

    :param dep: the department selected by the user
    :type dep: str
    :return: dep.html
    :rtype: n/a
    """

    if session["user"]:
        dep = dep
        # get selected department collection's data from Mongo
        depart = list(mongo.db[dep].find().sort('date', -1))

        # Render the Department by Date page
        return render_template(
            "dep.html", dep=dep, depart=depart, day="All Messages")


@app.route("/find_all/<dep>")
def find_all(dep):
    """Render the Department by Poster page with all messages for
    choosen department.

    Renders the Department page with all messages for the choosen department
    getting that department's messages from Mongo.

    :param dep: the department selected by the user
    :type dep: str
    :return: dep_poster.html
    :rtype: n/a
    """

    if session["user"]:
        dep = dep
        # get selected department collection's data from Mongo
        depart = list(mongo.db[dep].find().sort('date', -1))

        # Render the Department by Poster page
        return render_template(
            "dep-poster.html", dep=dep, depart=depart, day="All Messages")


@app.route("/all_images/")
def all_images():
    """Render the Images page.

    Renders the Images page with all images showing
    getting the images from Mongo.

    :return: images.html
    :rtype: n/a
    """

    if session["user"]:
        # get images collection's data from Mongo
        images = list(mongo.db.images.find())
        # Render the Images page
        return render_template("images.html", images=images)


@app.route("/get_image/", methods=["GET", "POST"])
def get_image():
    """Render the Images page.

    On Get renders the Images page.
    On Post renders the Images page with image or images selected
    from a user's query,
    getting the images from Mongo.

    :return: images.html
    :rtype: n/a
    """

    if session["user"]:
        if request.method == "POST":
            image = request.form.get("image")
            # get images collection's documents matching search queries
            # from Mongo
            images = list(mongo.db.images.find({"$text": {"$search": image}}))
            # Render the Images page
            return render_template("images.html", images=images)

        # get image with name "windowlight" from images collection from Mongo
        images = list(mongo.db.images.find({"image_name": "windowlight"}))
        # Render the Images page
        return render_template("images.html", images=images)


@app.route("/logout")
def logout():
    """Logs the user out.

    Removes the user from sesson user
    and renders the login page.

    :return: login.html
    :rtype: n/a
    """

    if session["user"]:
        # delete user session cookie
        flash("Logout successful")
        session.pop("user")
        # Render the Login page
        return redirect(url_for("login"))


@app.route("/add_message", methods=["GET", "POST"])
def add_message():
    """Render the Add Message page.

    On Get renders the Add Message page.
    On Post creates a dictionary using values from the form, from datetime
    and from Mongo to create a new document in Mongo.

    :return: add_message.html
    :rtype: n/a
    """

    if session["user"]:
        if request.method == "POST":
            # get data from form
            mes_is_priority = "on" if request.form.get(
                "is_priority") else "off"
            mes_dept = request.form.get("department_name")
            # get date from datetime
            day = datetime.datetime.now()
            mes_date = day.strftime("%d %B, %Y")
            # get users collection data from Mongo
            user = mongo.db.users.find_one({"username": session["user"]})
            first = user["firstname"]
            last = user["lastname"]
            username = session["user"]
            mes_poster = f"{first} {last}"
            mes_job = user["job_title"]
            # create dictionary
            message = {
                "is_priority": mes_is_priority,
                "dept_name": mes_dept,
                "date": mes_date,
                "poster": mes_poster,
                "username": username,
                "job_title": mes_job,
                # get data from form
                "subject": request.form.get("subject"),
                "message": request.form.get("message"),
                "image_src": request.form.get("image_src"),
                "image_name": request.form.get("image_name"),
            }
            # insert document into selected department collection in Mongo
            mongo.db[mes_dept].insert_one(message)
            flash("Message Added")
            # Render the User Home page
            return redirect(url_for("user_home", username=session["user"]))

        depts = mongo.db.depts.find().sort("dept_name", 1)
        # Render the Add Messages page
        return render_template("add_message.html", depts=depts)


@app.route(
    "/edit_message/<message_id>/<depart>/<user>", methods=["GET", "POST"])
def edit_message(message_id, depart, user):
    """Render the Edit Message page.

    On Get checks if the message poster's username is equal to the sesson user
    or if admin2 is user and if either is true renders the Edit Message page
    with the selected message's detail as values in the input boxes..
    On Post creates a dictionary using values from the form, from datetime
    and from Mongo to update the selected message in Mongo.

    :param message_id: the selected document to be edited
    :type dep: str
    :param depart: the collection which the document is in
    :type dep: str
    :param user: the user's username
    :type dep: str
    :return: edit_message.html
    :rtype: n/a
    """

    if session["user"] == user or session["user"] == "admin2":
        if request.method == "POST":
            # get data from form
            mes_is_priority = "on" if request.form.get(
                "is_priority") else "off"
            # get date from datetime
            day = datetime.datetime.now()
            mes_date = day.strftime("%d %B, %Y")
            mes_dept = request.form.get("department_name")
            # get data from users collection in Mongo
            user = mongo.db.users.find_one({"username": session["user"]})
            username = session["user"]
            first = user["firstname"]
            last = user["lastname"]
            mes_poster = f"{first} {last}"
            mes_job = user["job_title"]
            # create dictionary
            edit = {
                "is_priority": mes_is_priority,
                "dept_name": mes_dept,
                "date": mes_date,
                "poster": mes_poster,
                "username": username,
                "job_title": mes_job,
                # get date from form
                "subject": request.form.get("subject"),
                "message": request.form.get("message"),
                "image_src": request.form.get("image_src"),
                "image_name": request.form.get("image_name"),
            }
            # update document in selected department collection in Mongo
            mongo.db[mes_dept].update({"_id": ObjectId(message_id)}, edit)
            flash("Message Updated")
            # Render the Department page
            return redirect(url_for("get_dep", dep=mes_dept))

        # get selected document in selected department collection in Mongo
        message = mongo.db[depart].find_one({"_id": ObjectId(message_id)})
        # get depts collection data from Mongo
        depts = mongo.db.depts.find().sort("dept_name", 1)
        # Render the Edit message page
        return render_template(
            "edit_message.html", message=message, depts=depts)


@app.route("/edit_image/<image_id>", methods=["GET", "POST"])
def edit_image(image_id):
    """Render the Edit Image page and allow admin to edit an image.

    On Get checks if admin2 is sesson user then renders the Edit Image page
    with the selected image's detail as values in the input boxes.
    On Post creates a dictionary using values from the form
    to update the selected document in Mongo.

    :param image_id: the selected document to be edited
    :type dep: str
    :return: edit_image.html
    :rtype: n/a
    """

    if session["user"] == "admin2":
        if request.method == "POST":
            edit = {
                "image_name": request.form.get("image_name"),
                "image_des": request.form.get("image_des"),
                "image_src": request.form.get("image_src")
            }
            # update selected document in images collection in Mongo
            mongo.db.images.update({"_id": ObjectId(image_id)}, edit)
            flash("Image Updated")
            # Render the Images page
            return redirect(url_for("get_image"))

        # get selected document in images collection in Mongo
        image = mongo.db.images.find_one({"_id": ObjectId(image_id)})
        # Render the Edit Images page
        return render_template("edit_image.html", image=image)


@app.route("/delete_message/<message_id>/<depart>/<user>")
def delete_message(message_id, depart, user):
    """Delete a Message.

    Checks if the message poster's username is equal to the sesson user
    or if admin2 is user and if either is true displays a model asking
    the user to confirm delete.
    If the user confirms the document is deleted in Mongo.

    :param message_id: the selected document to be deleted
    :type dep: str
    :param depart: the collection which the document is in
    :type dep: str
    :param user: the user's username
    :type dep: str
    :return: edit_message.html
    :rtype: n/a
    """

    if session["user"] == user or session["user"] == "admin2":
        # remove selected document from selected department collection in Mongo
        mongo.db[depart].remove({"_id": ObjectId(message_id)})
        flash("Message Deleted")
        # Render the Department page
        return redirect(url_for("get_dep", dep=depart))


@app.route("/guestadd_script")
def guestadd_script():
    """Guest admin update the script URL.

    On Get checks if admin is user and if true renders the Add Script page

    :return: add_script.html
    :rtype: n/a
    """

    if session["user"] == "admin":
        # Render the Add Script page
        return render_template("add_script.html")


@app.route("/add_script/<script_id>", methods=["GET", "POST"])
def add_script(script_id):
    """Update the script URL.

    On Get checks if admin is user and if true renders the Add Script page
    with the current script URL as a value in the input box.
    On Post the document is updated in Mongo.

    :param script_id: the selected document to be updated
    :type dep: str
    :return: edit_message.html
    :rtype: n/a
    """

    if session["user"] == "admin2":
        # get the one document from latest_script collection in Mongo
        script = list(mongo.db.latest_script.find())
        if request.method == "POST":
            latest = {
                "script": request.form.get("script_name")
            }
            # update the singular document in the latest_script collection
            # in Mongo
            mongo.db.latest_script.update(
                {"_id": ObjectId(script_id)}, latest)
            flash("Script Successfully Updated")
            # Render the User Home page
            return redirect(url_for("user_home", username=session["user"]))

        # Render the Add Script page
        return render_template("add_script.html", script=script)


@app.route("/guestadd_shot")
def guestadd_shot():
    """Guest admin update the shotlist URL.

    On Get checks if admin is user and if true renders the Add Shotlist page

    :return: add_shotlist.html
    :rtype: n/a
    """

    if session["user"] == "admin":
        # Render the Add Shotlist page
        return render_template("add_shotlist.html")


@app.route("/add_shot", methods=["GET", "POST"])
def add_shot():
    """Update the shotlist URL.

    On Get checks if admin2 is user and if true renders the Add Shotlist page
    On Post the document is updated in Mongo.

    :return: add_shotlist.html
    :rtype: n/a
    """

    if session["user"] == "admin2":
        if request.method == "POST":
            newshot = {
                "shotlist": request.form.get("shot_name")
            }
            # update the singular document in the shotlist collection in Mongo
            mongo.db.shotlist.update(
                {"_id": ObjectId("6029b7f80febec6e0f942fcb")}, newshot)
            flash("Shotlist Successfully Updated")
            # Render the User Home page
            return redirect(url_for("user_home", username=session["user"]))

        # Render the Add Shotlist page
        return render_template("add_shotlist.html")


@app.route("/guestadd_image")
def guestadd_image():
    """Display for guest admin the add image page.

    On Get checks if admin is user and if true renders the Add Image page.

    :return: add_image.html
    :rtype: n/a
    """

    if session["user"] == "admin":
        # Render the Add Image page
        return render_template("add_image.html")


@app.route("/add_image", methods=["GET", "POST"])
def add_image():
    """Update the script URL.

    On Get checks if admin2 is user and if true renders the Add Image page
    On Post the document is updated in Mongo.

    :return: add_image.html
    :rtype: n/a
    """

    if session["user"] == "admin2":
        if request.method == "POST":
            new_image = {
                "image_name": request.form.get("image_name"),
                "image_des": request.form.get("image_des"),
                "image_src": request.form.get("image_src")
            }
            # add a new document to the images collection in Mongo
            mongo.db.images.insert_one(new_image)
            flash("Image Added")
            # Render the User Home page
            return redirect(url_for("user_home", username=session["user"]))

        # Render the Add Image page
        return render_template("add_image.html")


@app.route("/guestremove_user")
def guestremove_user():
    """Guest admin remove user.

    Checks if admin is user and if true renders the remove user page

    :return: userbase.html
    :rtype: n/a
    """

    if session["user"] == "admin":
        # Render the Remove User page
        return render_template("remove_user.html")


@app.route("/remove_user", methods=["GET", "POST"])
def remove_user():
    """Remove a user.

    On Get checks if admin2 is user and if true renders the remove user page
    On Post the user is removed in Mongo.

    :return: userhome..html
    :rtype: n/a
    """

    if session["user"] == "admin2":
        if request.method == "POST":
            # remove document from the users collection in Mongo
            mongo.db.users.remove({"firstname": request.form.get(
                "first_name"), "lastname": request.form.get("last_name")})
            flash("User Successfully Removed")
            # Render the User Base page
            return redirect(url_for("user_home", username=session["user"]))

        # Render the Remove User page
        return render_template("realremove_user.html")


@app.route("/delete_image/<image_id>")
def delete_image(image_id):
    """Delete an image.

    On Get checks if admin2 is user then the document is deleted in Mongo.

    :param image_id: the selected document to be deleted
    :type dep: str
    :return: images.html
    :rtype: n/a
    """

    if session["user"] == "admin2":
        # delete document in the images collection in Mongo
        mongo.db.images.delete_one({"_id": ObjectId(image_id)})
        flash("Image Removed")
        # render Images page
        return redirect(url_for("get_image"))


@app.errorhandler(404)
def page_not_found(e):
    """Render 404 page.

    When an error message occur render the 404.html page.

    :param 404: the error code
    :param e: the error code
    :type temp: integer
    :return: 404.html
    :rtype: n/a
    """

    if session["user"]:
        # render 404 page
        return render_template('404.html'), 404


@app.errorhandler(500)
def server_er(e):
    """Render 500 page.

    When a 500 error message occurs render the 500.html page.

    :param 500: the error code
    :param e: the error code
    :type temp: integer
    :return: 500.html
    :rtype: n/a
    """

    if session["user"]:
        # render 500 page
        return render_template('404.html'), 500


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)
