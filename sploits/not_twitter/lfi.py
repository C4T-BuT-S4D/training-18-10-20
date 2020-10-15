#!/usr/bin/env python3
import sys
import secrets
from requests import Session
import re

limit = 128
offset = 0

ip = sys.argv[1]
find_fileinfo_regexp = re.compile(r'<div class="filenames">(.*)</div>')
new_filename_link = re.compile(r'<div class="message">Ваш фанфик был загружен на (uploads/.*)</div>')

url = f'http://{ip}:3113'
login = secrets.token_hex(10)
password = login

s = Session()
resp = s.post(url + '/register', data = {'login':login, 'password': password})
resp = s.post(url + '/login', data = {'login':login, 'password': password})

#get file listing
uploads_html = s.get(url + f'/uploads?limit={limit}&offset={offset}').text
files_info = find_fileinfo_regexp.findall(uploads_html)
filenames = [f"{x.split(': ')[0]}_{x.split(': ')[1]}" for x in files_info]

#for every file upload new by link 'file:///services/not_twitter/uploads' + old filename

copy_filenames = []

for filename in filenames:
    link = f"file:///services/not_twitter/uploads/{filename}"
    r = s.post(url + '/upload_by_link', data = {'link':link})
    new_link = new_filename_link.findall(r.text)[0]
    copy_filenames.append(new_link)

#download all new files

for filename in copy_filenames:
    print(s.get(url + '/' + filename).text)