import urllib.request
import os
import secrets
from flask import Flask, flash, request, redirect, url_for, send_from_directory, render_template, session, send_file
from werkzeug.utils import secure_filename
from functools import wraps
import user_model
from helpers import *
import redis_controller
import database_controller

default_upload_folder = 'C://workspace/ctf/dev/training-XX-YY-ZZZZ/services/not_twitter/uploads'
UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", default_upload_folder)
MAX_FILESIZE = 1024
MAX_FILE_COUNT_IN_LISTING = 128

app = Flask(__name__)
app.secret_key = "useless_key"

def check_auth():
    try:
        cookie = session["user"]
        print(f"cookie is {cookie}")
        if not user_model.check_auth(cookie):
            return False
        return True
    except KeyError:
        return False

@app.route('/')
def hello_world():
    return redirect(url_for('upload_text'))

@app.route('/upload_by_link', methods=['GET', 'POST'])
def upload_file():
    if not check_auth():
        return redirect(url_for('login'))
    if request.method == 'POST':
        link = request.form['link']
        try:
            file_resp = urllib.request.urlopen(link)
            file_bytes = file_resp.read(MAX_FILESIZE)
        except Exception:
            message = f"Error during downloading the page"
            return render_template('message.html', message=message)
        if file_bytes:
            cookie = session["user"]
            user_model.check_auth(cookie)
            #print("cookie is", cookie, flush=True)
            username = redis_controller.get_username_by_cookie(cookie)
            #print(cookie, username, flush=True)
            filename = username + '_' + secrets.token_hex(10) + '.txt'
            with open(os.path.join(UPLOAD_FOLDER, filename), 'wb+') as f:
                f.write(file_bytes)
            message= f"Your fanfic was uploaded to uploads/{filename}"
            return render_template('message.html', message=message)
        else:
            return "Empty file"
    return render_template('upload_get.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload_text():
    if not check_auth():
        return redirect(url_for('login'))
    if request.method == 'POST':
        text = request.form['text']
        if text:
            cookie = session["user"]
            user_model.check_auth(cookie)
            #print("cookie is", cookie, flush=True)
            username = redis_controller.get_username_by_cookie(cookie)
            #print(cookie, username, flush=True)
            filename = username + '_' + secrets.token_hex(10) + '.txt'
            with open(os.path.join(UPLOAD_FOLDER, filename), 'w+') as f:
                f.write(text)
            message = f"Your fanfic was uploaded to uploads/{filename}"
            return render_template('message.html', message=message)
        else:
            message = "Empty file"
            return render_template('message.html', message=message), 400
    return render_template('upload_get_text.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login = request.form['login']
        password = request.form['password']
        print(f"log {login}, pass {password}")
        try:
            user = user_model.User(login, password)
            print(f"login {user}", flush=True)
            with database_controller.DatabaseClient() as db:
                print(f"all users {db.get_all_users()}")
                if not db.check_user(user):
                    message = "There is no such user in db"
                    return render_template('message.html', message=message), 400
            session['user'] = user.cookie
            redis_controller.add_to_store(login, session['user'])
            return redirect(url_for('upload_text'))
        except ValueError:
            message= "Incorrect username"
            return render_template('message.html', message=message), 403
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        login = request.form['login']
        password = request.form['password']
        print(f"log {login}, pass {password}")
        try:
            user = user_model.User(login, password)
            print(f"login {user}", flush=True)
            with database_controller.DatabaseClient() as db:
                db.add_user(user)
            session['user'] = user.cookie
            redis_controller.add_to_store(login, session['user'])
            return redirect(url_for('upload_file'))
        except ValueError:
            message = "Incorrect username"
            return render_template('message.html', message=message), 403
    return render_template('register.html')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    if not check_auth():
        return redirect(url_for('login'))
    cookie = session['user']
    username = redis_controller.get_username_by_cookie(cookie)
    print(f"upl_file username {username}")
    if filename.split('_')[0]==username:
        return send_from_directory(UPLOAD_FOLDER, filename)
    else:
        message = "Forbidden"
        return render_template('message.html', message=message), 403

@app.route('/uploads/')
def file_listing():
    try:
        limit = int(request.args.get('limit'))
        if limit > MAX_FILE_COUNT_IN_LISTING:
            message = "Limit is too big"
            return render_template('message.html', message=message), 400
        offset = int(request.args.get('offset'))
    except TypeError:
        limit = MAX_FILE_COUNT_IN_LISTING
        offset=0
    username = request.args.get('user')
    print(f"uploads args: offset {offset}, limit {limit}, username {username}")
    if username is None:
        files = listdir_fileclass(offset, limit)
    else:
        files = listdir_fileclass_by_user(offset, limit, username)
    print(f"files {[x.filename for x in files]}")
    return render_template('uploads.html', files=files)

if __name__ == "__main__":
    app.run(host="0.0.0.0")
