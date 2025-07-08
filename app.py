from decorators import login_required
from flask import Flask, flash, redirect, render_template, request, session, jsonify
from flask_session import Session
from cs50 import SQL

app = Flask(__name__)

app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

# abro base de datos
db = SQL("sqlite:///users.db")


@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    # load posts
    posts = db.execute(
        "select * from posts join users on posts.user_id = users.id where type = 'main' order by post_id desc")
    user = db.execute("select * from users where id = ?",
                          session["user_id"])
    if request.method == "GET":
        type = request.args.get("add_post")

        return render_template("index.html", username=user[0]["name"] + " " + user[0]["surname"], posts=posts, len=len(posts), type = type)
    if request.method == "POST":
        data = request.form.get("data")
        if data:
            db.execute("insert into posts (body,user_id) values (?,?)", data, session["user_id"])
    return redirect("/")

@app.route("/post", methods=["GET", "POST"])
@login_required
def post():
    if request.method == "GET":
        post_id = request.args.get("post_id")
        if post_id == None:
            return redirect("/")
        post = db.execute("select * from posts join users on posts.user_id = users.id where post_id = ? ",post_id)
        comments = db.execute(
        "select * from posts join users on posts.user_id = users.id where type = 'comment' and reference_post = ? order by post_id desc",post_id)

        return render_template("post.html",post=post,comments=comments,len=len(comments),post_id=post_id)
    if request.method == "POST":
        post_id = request.form.get("post_id")
        comment = request.form.get("comment")
        comment_data = request.form.get("comment_data")
        delete = request.form.get("delete")
        delete_data = request.form.get("delete_data")
        edit = request.form.get("edit")
        edit_data = request.form.get("edit_data")
        post = db.execute("select * from posts join users on posts.user_id = users.id where post_id = ? ",post_id)
        if comment:
            return render_template("post.html",post=post,post_id=post_id,comment=comment,len=0)
        if comment_data:
            if not db.execute("select * from posts where body = ? and user_id = ? and type = ? and reference_post = ?",comment_data,session["user_id"],"comment",post_id):
                db.execute("insert into posts (body,user_id,type,reference_post) values(?,?,?,?)",comment_data,session["user_id"],"comment",post_id)
            return redirect("/post?post_id="+str(post_id))
        if edit:
            return render_template("post.html",post=post,post_id=post_id,edit=edit,len=0)
        if delete:
            return render_template("post.html",post=post,post_id=post_id,delete=delete,len=0)
        if delete_data:
            if db.execute("select * from posts where post_id = ? or reference_post = ?",post_id,post_id):
                flash("succesfuly deleted!")
                db.execute("delete from posts where post_id = ? or reference_post = ?",post_id,post_id)
            return redirect("/")
        if edit_data:
            db.execute("update posts set body = ? where post_id = ?",edit_data,post_id)

            return redirect("/post?post_id="+str(post_id))
        return redirect("/post?post_id="+str(post_id))


@app.route("/notifications", methods=["GET", "POST"])
@login_required
def notifications():
    notifications = db.execute("select * from notifications where user_id = ?", session["user_id"])
    print(notifications)
    if request.method == "GET":
        return render_template("notifications.html", notifications=notifications)


@app.route("/friends", methods=["GET", "POST"])
@login_required
def friends():
    if request.method == "GET":
        # select from friends where user_id is involved
        friend = db.execute(
            "select * from friends where confirmation like ?", "%" + str(session["user_id"]) + "%")
        friends = []
        for f in friend:
            # if friends
            if len(f["confirmation"]) > len(str(session["user_id"])) + 1:

                find_id = f["confirmation"].split("_")

                find_id.remove(str(session["user_id"]))
                friend_data = db.execute("select * from users where id = ?", find_id[0])
                friends.append(friend_data)

        return render_template("friends.html", friends=friends, len=len(friends))


@app.route("/messages", methods=["GET", "POST"])
@login_required
def messages():
    if request.method == "GET":

        return render_template("messages.html")


@app.route("/manage_accounts", methods=["GET", "POST"])
@login_required
def manage_accounts():
    if request.method == "GET":
        user = db.execute("select * from users where id = ?",
                          session["user_id"])
        return render_template("manage_accounts.html", username=user[0]["name"] + " " + user[0]["surname"])
    if request.method == "POST":
        db.execute("delete from users where id = ?", session["user_id"])
        db.execute("delete from posts where user_id = ?", session["user_id"])
        db.execute("delete from friends where id like ?", "%" + str(session["user_id"]) + "%")
        db.execute("delete from notifications where user_id = ?", session["user_id"])
        flash("Account deleted")
        return redirect("/logout")


@app.route("/search", methods=["GET", "POST"])
@login_required
def search():
    # search using python instead of sql
    if request.method == "GET":
        name = request.args.get("name")
        # if username not provided
        if not name:
            return render_template("search.html")
        # asign user data to a variable
        users = db.execute(
            "select * from users where name like ? or surname like ? or username = ?", "%" + name + "%", "%" + name + "%", "%" + name + "%")
        # check if username in database
        if not users:
            flash("User not found")
            return redirect("/search")
        session["foreign_user"] = users[0]["username"]
        return render_template("search.html", users=users)

# friends states:
# 0 none
# 1 waiting
# 2 friends


@app.route("/homepage", methods=["GET", "POST"])
@login_required
def homepage():
    username = request.args.get("username")
    commons = []
    their_friends = []
    if not username:
        return redirect("/")
    posts = db.execute(
        "select * from posts p join users s on s.id = p.user_id where username = ? order by post_id desc", username)

    select = db.execute("select * from users where username = ?", username)
    user = db.execute("select * from users where id = ?", session["user_id"])
    if select[0]["id"] != session["user_id"]:
        if select[0]["id"] < session["user_id"]:
            id = str(select[0]["id"])+"_"+str(session["user_id"])
            pos = "last"
        if select[0]["id"] > session["user_id"]:
            id = str(session["user_id"])+"_"+str(select[0]["id"])
            pos = "first"

        lengt = db.execute("select * from friends where id = ?", id)

        # if id in database
        if len(lengt) != 0:
            length = lengt[0]["confirmation"]
            print(len(length), len(str(session["user_id"])) + 1)
            if len(length) == 1:
                friends = 0
            if len(length) == len(str(session["user_id"])) + 1:
                friends = 1
            if len(length) > len(str(session["user_id"])) + 1:
                friends = 2
            print(f"confirmation : {length} friend value : {friends}")
            # if not create one
        if len(lengt) == 0:
            friends = 0
    else:
        friends = "NULL"
    if request.method == "GET":

        # if username was not provided handle it by giving it foreign_user's value

        select = db.execute("select * from users where username = ?", username)
        # asign foreign_user value to the one provided

        session["foreign_user"] = username

        # TODO

        # look up username's rating in database
        # select all of my friends
        friend = db.execute(
            "select * from friends where confirmation like ?", "%" + str(session["user_id"]) + "%")
        my_friends = []
        for f in friend:
            # check if we friends
            if len(f["confirmation"]) > len(str(session["user_id"])) + 1:

                # separate id from confirmation
                find_id = f["confirmation"].split("_")

                find_id.remove(str(session["user_id"]))
                # get all of my friend's data
                friend_data = db.execute("select * from users where id = ?", find_id[0])
                # add my friend to my friends list
                my_friends.append(friend_data)

        # select their data
        friendship = db.execute(
            "select confirmation from friends where confirmation like ?", "%" + str(select[0]["id"]) + "%")
        # check one by one their friends
        for friendsh in friendship:
            # check confirmation
            stri = friendsh["confirmation"].split("_")
            stri.remove(str(select[0]["id"]))
            try:
                stri.index("")
            except ValueError:
                # if their friend is not us
                if stri[0] != str(session["user_id"]):
                    common = db.execute("select * from users where id = ?", stri[0])
                    their_friends.append(common)
                    for i in my_friends:
                        print("common[0]", common[0])
                        if common[0]["id"] == i[0]["id"]:
                            commons.append(common)
                            break
            else:
                continue
        print("commons", commons)
        return render_template("homepage.html", user=select, friends=friends, posts=posts, len=len(posts), commons=commons, len_commons=len(commons), their_friends=their_friends)

    if request.method == 'POST':
        add = request.form.get("add")
        if add == "True" and friends != "NULL":
            # addFriend
            # check for username id in database

            # check if username and user are friends
            # pos says where our id goes:
            # before or after underscore

            check = db.execute("select * from friends where id = ?", id)

            # if friends
            if len(check) > 0:
                index = check[0]["confirmation"].find(str(session["user_id"]))
                # check for user_id
                # index == -1 menas user hasnt sent friend request
                if index == -1:
                    if pos == "first":
                        db.execute("update friends set confirmation = ? where id = ?", str(
                            session["user_id"])+check[0]["confirmation"], id)

                    if pos == "last":
                        db.execute("update friends set confirmation = ? where id = ?",
                                   check[0]["confirmation"]+str(session["user_id"]), id)
                    if not db.execute("select * from notifications where data = ? and user_id = ?", user[0]["username"] + " has sent you a friend request!", select[0]["id"]):
                        print(db.execute("select * from notifications where data = ? and user_id = ?",
                              user[0]["username"] + " has sent you a friend request!", select[0]["id"]))
                        db.execute("insert into notifications (data,user_id) values(?,?)",
                                   user[0]["username"] + " has sent you a friend request!", select[0]["id"])
                # else means user has sent request AKA cancel friendship
                else:
                    # split
                    split = check[0]["confirmation"].split("_")
                    if pos == "first":
                        db.execute(
                            "update friends set confirmation = ? where id = ?", "_"+split[1], id)
                    if pos == "last":
                        db.execute(
                            "update friends set confirmation = ? where id = ?", split[0]+"_", id)
                    if not db.execute("select * from notifications where data = ? and user_id = ?", user[0]["username"] + " is not your friend anymore!", select[0]["id"]):
                        db.execute("insert into notifications (data,user_id) values(?,?)",
                                   user[0]["username"] + " is not your friend anymore!", select[0]["id"])

            # if not friends
            # create new row

            # probably herre
            if len(check) == 0:
                if pos == "first":
                    db.execute("insert into friends (id,confirmation) values (?,?)", id, str(
                        session["user_id"])+"_")
                if pos == "last":
                    db.execute("insert into friends (id,confirmation) values (?,?)",
                               id, "_"+str(session["user_id"]))
                if not db.execute("select * from notifications where data = ? and user_id = ?", user[0]["username"] + " has sent you a friend request!", select[0]["id"]):
                    db.execute("insert into notifications (data,user_id) values(?,?)",
                               user[0]["username"] + " has sent you a friend request!", select[0]["id"])

            if select[0]["id"] != session["user_id"]:
                if select[0]["id"] < session["user_id"]:
                    id = str(select[0]["id"])+"_"+str(session["user_id"])
                    pos = "last"
                if select[0]["id"] > session["user_id"]:
                    id = str(session["user_id"])+"_"+str(select[0]["id"])
                    pos = "first"

                length = db.execute(
                    "select * from friends where id = ?", id)[0]["confirmation"]
                print(len(length), len(str(session["user_id"])) + 1)
                if len(length) == 1:
                    friends = 0
                if len(length) == len(str(session["user_id"])) + 1:
                    friends = 1
                if len(length) > len(str(session["user_id"])) + 1:
                    friends = 2
                print(f"confirmation : {length} friend value : {friends}")
                # return jsonify(mensajes = "ola pelota")
        return redirect("/homepage?username="+username)
    return render_template("homepage.html", user=select, friends=friends, posts=posts, len=len(posts), commons=commons, len_commons=len(commons), their_friends=their_friends)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html",username = "")
    if request.method == "POST":
        # asign user input to variables
        username = request.form.get("username")
        password = request.form.get("password")
        # check empty fields
        if not password or not username:
            flash("Empty fields")
            return redirect("/login")
        # asign user table to variable
        user = db.execute("select * from users where username = ?", username)
        # look for user in database
        if not user:
            flash("Couldn't succesfully find account.")
            return render_template("login.html",username = username)
        # check password
        elif password != user[0]["password"]:
            flash("Wrong Username or Password. Try again or Change Password.")
            return render_template("login.html",username = username)
        session["user_id"] = user[0]["id"]
        session["username"] = user[0]["username"]
        print(session["username"])
        return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html",name = "", surname = "", username = "")
    if request.method == "POST":
        name = request.form.get("name")
        surname = request.form.get("surname")
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        if not (name and surname and username and password):
            flash("Please fill all the fields.")
        if db.execute("select * from users where username = ?", username):
            flash("Username already exists.")
        if password != confirmation:
            flash("Confirmation does not match password.")
        if name and surname  and username and password and not db.execute("select * from users where username = ?", username) and password == confirmation:
            try:
                db.execute("insert into users (name,surname,username,password) values (?,?,?,?)",
                           name, surname, username, password)
            except:
                flash("An error happened.")
                return redirect("/register")
            else:
                # db.execute("insert into users (name,surname,username,password) values (?,?,?,?,?)",name,surname,username,password)
                user = db.execute(
                    "select * from users where username = ?", username)
                session["user_id"] = user[0]["id"]
                session["username"] = user[0]["username"]
                flash("succesfully registered!")
                return redirect("/")
    return render_template("register.html",name = name, surname = surname,  username = username)

@app.route("/logout")
@login_required
def logout():
    session.clear()
    session["username"] = ""
    print(session)
    return redirect("/")
