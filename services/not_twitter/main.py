import urllib.request
import os
import secrets
from flask import Flask, flash, request, redirect, url_for, send_from_directory, render_template
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'uploads'
MAX_FILESIZE = 1024

app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello, World!'

@app.route('/check')
def return_html():
    link = request.args.get('link')
    return f"your link:\n{urllib.request.urlopen(link).read()}"

@app.route('/upload_by_link', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        link = request.form['link']
        file_resp = urllib.request.urlopen(link)
        print(file_resp)
        file_bytes = file_resp.read(MAX_FILESIZE)
        if file_bytes:
            filename = secrets.token_hex(10) + '.txt'
            with open(os.path.join(UPLOAD_FOLDER, filename), 'wb+') as f:
                f.write(file_bytes)
            return f"your file uploaded to 'uploads/{filename}'"
        else:
            return "no file"
    return render_template('upload_get.html')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER,
                               filename)

if __name__ == "__main__":
    app.run(debug=True, port = 5000)
