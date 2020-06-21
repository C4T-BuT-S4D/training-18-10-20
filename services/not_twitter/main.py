import urllib.request
import os
import secrets
from flask import Flask, flash, request, redirect, url_for, send_from_directory, render_template, session, send_file
from werkzeug.utils import secure_filename
import user_model
from helpers import *

UPLOAD_FOLDER = 'C://workspace/ctf/dev/training-XX-YY-ZZZZ/services/not_twitter/uploads'
#UPLOAD_FOLDER = '/services/not_twitter'
MAX_FILESIZE = 1024

app = Flask(__name__)
app.secret_key = "useless_key"

@app.route('/')
def hello_world():
    return 'Hello, World!'

@app.route('/upload_by_link', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        link = request.form['link']
        file_resp = urllib.request.urlopen(link)
        print(file_resp)
        file_bytes = file_resp.read(MAX_FILESIZE)
        if file_bytes:
            username = session['user']
            filename = username + '_' + secrets.token_hex(10) + '.txt'
            with open(os.path.join(UPLOAD_FOLDER, filename), 'wb+') as f:
                f.write(file_bytes)
            return f"your file uploaded to 'uploads/{filename}'"
        else:
            return "no file"
    return render_template('upload_get.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login = request.form['login']
        password = request.form['password']
        print(login, password)
        #user = user_model.User(login, password)
        session['user'] = login
        return redirect(url_for('upload_file'))
    return render_template('login.html')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    username = session['user']
    if filename.split('_')[0]==username:
        return send_from_directory(UPLOAD_FOLDER, filename)
    else:
        return "Not yours", 403

@app.route('/uploads/')
def file_listing():
    files = get_only_new_files()
    print(files)
    files_str = [f"{x.user}: {x.filename}" for x in get_only_new_files()]
    return '\n'.join(files_str)

if __name__ == "__main__":
    app.run(debug=True, port = 5000)
