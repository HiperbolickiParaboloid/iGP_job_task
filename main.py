from flask import Flask, render_template, redirect, url_for, request, flash, jsonify, Response
from functools import wraps
from db_config import cursor, conn
from flask_jwt import current_identity
from passlib.hash import argon2
import datetime, jwt

app = Flask(__name__, template_folder= "templates")
app.config['SECRET_KEY'] = 'my_own_secret_key'


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        #print(token)
        try:
            token = request.cookies['JWT']
            data = jwt.decode(token, app.config['SECRET_KEY'])
            #print (data)
        except:
            flash('You have successfuly logged out from your bSocial account, or your session has been expired.')
            return redirect(url_for("login"))
            #return jsonify({'message': 'Token is invalid.'})
        return f(*args, **kwargs)
    return decorated

@app.route("/signup", methods = ["GET","POST"])
def signup():
    if request.method == "POST":
        name = request.form["Name"]
        surname = request.form["Surname"]
        username = request.form["Username"]
        email = request.form["email"]
        password = request.form["Password"]
        confirm_password = request.form["ConfirmPassword"]
        if password != confirm_password:
            flash("Passwords doesn't match. Please check.")
            return redirect(request.url)
        else:
            try:
                cursor.execute("SELECT * from users WHERE username = %s", (username,))
                username_check = cursor.fetchall()
            except Exception as identifier:
                username_check = cursor.fetchall()
            try:
                cursor.execute("SELECT * from users WHERE email = %s", (email,))
                email_check = cursor.fetchall()
            except Exception as identifier:
                email_check = cursor.fetchall()
            if not username_check:
                if not email_check:
                    hash_password = argon2.hash(password)
                    cursor.execute("""INSERT INTO users (name, surname, username, email, password) VALUES (%s, %s, %s, %s, %s)""", (name, surname, username, email, hash_password))
                    conn.commit()
                    #flash("Account has been created. Proceed with signing in.")
                    return render_template("successful_reg.html")
                else:
                    flash("Email already exists. Please use another one.")
                    return redirect(request.url)
            else:
                flash("Username already exists. Please use another one.")
                return redirect(request.url)
    return render_template("registration.html")

@app.route("/", methods = ["GET", "POST"])
def login():
    if request.method == "POST":
        username_email = request.form["login_string"]
        password = request.form["Password"]
        try:
            cursor.execute("SELECT * from users WHERE username = %s", (username_email,))
            user_check_1 = cursor.fetchall()
        except Exception as identifier:
            user_check_1 = cursor.fetchall()
        #print(user_check_1)
        try:
            cursor.execute("SELECT * from users WHERE email = %s", (username_email,))
            user_check_2 = cursor.fetchall()
        except Exception as identifier:
            user_check_2 = cursor.fetchall()
        #print(user_check_2)
        if user_check_1 == []:
            user_check = user_check_2
        else:
            user_check = user_check_1
        #print (user_check)
        #print (user_check[0][4])
        if user_check:
            if argon2.verify(password, user_check[0][4]) == True:
                token = jwt.encode({'user': user_check[0][2], 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=5)}, app.config['SECRET_KEY'])
                #return jsonify({'token': token.decode('UTF-8')})
                response = redirect(url_for('home'))
                response.set_cookie('JWT', token)
                return response
            else:
                flash("Incorrect password. Please try again.")
                return redirect(request.url)
        else:
            flash("User with specified username or email does not exist. Check your spelling or please Sign Up.")
            return redirect(request.url)
    return render_template("login.html")

@app.route("/logout", methods = ["GET", "POST"])
def logout():
    response = redirect(url_for('home'))
    response.set_cookie('JWT', '', expires=0)
    #flash ('You have successfuly logged out from your bSocial account, or your session has been expired.')
    return response

@app.route("/home", methods = ["GET", "POST"])
@token_required
def home():
    token = request.cookies['JWT']
    data = jwt.decode(token, app.config['SECRET_KEY'])
    current_user = data['user']
    if request.method == "POST":
        post_text = request.form["post_text"]
        post_privacy = request.form["post_privacy"]
        time = datetime.datetime.utcnow()
        print(time)
        #print (post_privacy, current_user, post_text)
        cursor.execute("""INSERT INTO posts (user_username, post, post_privacy, datetime) VALUES (%s, %s, %s, %s);""", (current_user, post_text, post_privacy, time))
        conn.commit()
    try:
        cursor.execute("""SELECT * FROM posts 
        WHERE user_username IN (SELECT follows FROM followers WHERE username = %s)
        union
        SELECT * FROM posts WHERE post_privacy = 'public'
        ORDER BY id_post DESC
        """, (current_user,))
        data = cursor.fetchall()
        return render_template("home.html", data=data)
    except Exception as identifier:
        print ('No data!')
        return render_template("home.html")
    

@app.route("/<string:username>", methods = ["GET", "POST"])
@token_required
def profile(username):
    token = request.cookies['JWT']
    token_decoded = jwt.decode(token, app.config['SECRET_KEY'])
    current_user = token_decoded['user']
    try:
        cursor.execute("""SELECT follows FROM followers WHERE username=%s AND follows=%s;""", (current_user, username))
        following = cursor.fetchall()
    except Exception as identifier:
        following = cursor.fetchall()
    if following:
        try:
            cursor.execute("""SELECT * FROM posts WHERE user_username = %s ORDER BY id_post DESC;""", (username,))
            data = cursor.fetchall()
        except Exception as identifier:
            pass
        if data == []:
            data = [(username, 'No posts to show!'), False]
        if request.method == "POST":
            cursor.execute("""DELETE FROM followers WHERE username = %s AND follows = %s;""", (current_user, username))
            conn.commit()
            try:
                cursor.execute("""SELECT * FROM posts WHERE user_username = %s AND post_privacy = %s ORDER BY id_post DESC;""", (username, 'public'))
                data = cursor.fetchall()
            except Exception as identifier:
                pass
            if data == []:
                data = [(username, 'No posts to show!'), False]
            return render_template('nfprofile.html', data=data)
        return render_template("fprofile.html", data=data)
    else:
        try:
            cursor.execute("""SELECT * FROM posts WHERE user_username = %s AND post_privacy = %s ORDER BY id_post DESC;""", (username,  'public'))
            data = cursor.fetchall()
        except Exception as identifier:
            pass
        if data == []:
            data = [(username, 'No posts to show!'), False]
        if request.method == "POST":
            cursor.execute("""INSERT INTO followers (username, follows) VALUES (%s,%s);""", (current_user, username))
            conn.commit()
            try:
                cursor.execute("""SELECT * FROM posts WHERE user_username = %s ORDER BY id_post DESC;""", (username,))
                data = cursor.fetchall()
            except Exception as identifier:
                pass
            if data == []:
                data = [(username, 'No posts to show!'), False]
            return render_template('fprofile.html', data=data)
        return render_template("nfprofile.html", data=data)

@app.route("/posts/<string:id>", methods = ["GET", "POST"])
@token_required
def post(id):
    if request.method == "POST":
        comment_text = request.form["comment_text"]
        #print(comment_text)
        token = request.cookies['JWT']
        token_decoded = jwt.decode(token, app.config['SECRET_KEY'])
        current_user = token_decoded['user']
        time = datetime.datetime.utcnow()
        #print(current_user)
        cursor.execute("""INSERT INTO comments (username, post_id, comment, datetime) VALUES (%s,%s,%s,%s);""", (current_user, id, comment_text, time))
        conn.commit()
    cursor.execute("""SELECT * FROM posts WHERE id_post = %s;""", (id,))
    data_1 = cursor.fetchall()
    cursor.execute("""SELECT * FROM comments WHERE post_id = %s;""", (id,))
    data_2 = cursor.fetchall()
    data=[data_1,data_2]
    return render_template("post.html", data=data)


@app.route("/test", methods = ["GET", "POST"])
@token_required
def test():
    return render_template("profile.html")

if __name__ == "__main__":
    app.run(debug=True)