import base64

from checklib import *
import requests

PORT = 8000


class CheckMachine:
    @property
    def url(self):
        return f'http://{self.c.host}:{self.port}'

    @property
    def api_url(self):
        return f'{self.url}/api'

    def __init__(self, c: BaseChecker):
        self.c = c
        self.port = PORT

    def register_user(self, email=None, password=None):
        email = email or rnd_username() + '@cbsctf.live'
        password = password or rnd_password()

        sess = self.c.get_initialized_session()

        r = sess.post(f'{self.api_url}/register', json={'email': email, 'password': password})
        self.c.check_response(r, 'Could not register')
        return email, password, sess

    def login_user(self, email, password):
        sess = self.c.get_initialized_session()
        r = sess.post(f'{self.api_url}/login', json={'email': email, 'password': password})
        self.c.check_response(r, 'Could not login')
        return sess

    def create_meeting(self, sess: requests.Session, title, desc, capacity=5, image_file=None, image_url=None,
                       image_params=None):
        data = {'title': title, 'description': desc, 'capacity': capacity}
        if image_url:
            data['image_url'] = image_url
        if image_params:
            data['image_params'] = image_params
        if image_file:
            data['image_base64'] = 'data:image/jpeg;base64,' + base64.b64encode(image_file.read()).decode()
            r = sess.post(f'{self.api_url}/sync', json=data)
        else:
            r = sess.post(f'{self.api_url}/sync', json=data)
        self.c.check_response(r, 'Could not create syncs')
        return self.c.get_json(r, 'Could not create syncs: invalid response type')

    def list_latest_meetings(self, sess: requests.Session = None):
        if not sess:
            sess = self.c.get_initialized_session()
        r = sess.get(f'{self.api_url}/syncs')
        self.c.check_response(r, 'Could not get latest syncs')
        return self.c.get_json(r, 'Could not get latest syncs. Invalid response type')

    def list_members(self, sess: requests.Session, m_id):
        r = sess.get(f'{self.api_url}/sync/{m_id}')
        self.c.check_response(r, 'Could not get sync members')
        return self.c.get_json(r, 'Could not get sync members. Invalid response type')

    def list_meetings(self, sess: requests.Session):
        r = sess.get(f'{self.api_url}/sync')
        self.c.check_response(r, 'Could not get user syncs')
        return self.c.get_json(r, 'Could not get user syncs. Invalid response type')

    def add_member(self, sess: requests.Session, m_id, nickname):
        if not sess:
            sess = self.c.get_initialized_session()

        r = sess.post(f'{self.api_url}/sync/{m_id}/join', json={'nickname': nickname})
        self.c.check_response(r, 'Could not add member to sync')
        return self.c.get_json(r, 'Could not add member to sync. Invalid response type')

    def get_ticket(self, sess: requests.Session, file_url):
        if not sess:
            sess = self.c.get_initialized_session()
        r = sess.get(f'{self.url}{file_url}')
        self.c.check_response(r, 'Could not get ticket')
        return r

    def get_ticket_data(self, sess: requests.Session, public_id):
        if not sess:
            sess = self.c.get_initialized_session()
        r = sess.get(f'{self.api_url}/ticket/' + public_id)
        self.c.check_response(r, 'Could not get ticket data')
        return self.c.get_json(r, 'Could not get ticket data. Invalid content type')

    def get_sync_info(self, sess: requests.Session, sync_id):
        if not sess:
            sess = self.c.get_initialized_session()
        r = sess.get(f'{self.api_url}/sync/{sync_id}/info')
        self.c.check_response(r, 'Could not get sync info')
        return self.c.get_json(r, 'Could not get sync info. Invalid content type')