#!/usr/bin/env python3
import sys
import secrets
from requests import Session
ip = sys.argv[1]

url = f'http://{ip}:3113'
login = secrets.token_hex(10)
password = login

s = Session()
resp = s.post(url + '/login', data = {'login':login, 'password': password})

#получить список файлов
#для каждого файла загрузить новый по адресу 'file:///services/not_twitter/uploads' + имя
#выкачать все эти файлы