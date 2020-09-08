#!/usr/bin/env python3
import sys
import secrets
from requests import Session
import re

ip = sys.argv[1]
find_fileinfo_regexp = re.compile(r'<div class="filenames">(.*)</div>')
new_filename_link = re.compile(r"Ваш фанфик был загружен на '(.*)'")

url = f'http://{ip}:3113'
login = secrets.token_hex(10)
password = login

s = Session()
resp = s.post(url + '/register', data = {'login':login, 'password': password})
resp = s.post(url + '/login', data = {'login':login, 'password': password})

#получить список файлов
uploads_html = s.get(url + '/uploads').text
files_info = find_fileinfo_regexp.findall(uploads_html)
filenames = [f"{x.split(': ')[0]}_{x.split(': ')[1]}" for x in files_info]

#для каждого файла загрузить новый по адресу 'file:///services/not_twitter/uploads' + имя

copy_filenames = []

for filename in filenames:
    link = f"file:///services/not_twitter/uploads/{filename}"
    r = s.post(url + '/upload_by_link', data = {'link':link})
    new_link = new_filename_link.findall(r.text)[0]
    copy_filenames.append(new_link)

#выкачать все эти файлы

for filename in copy_filenames:
    print(s.get(url + '/' + filename).text)