from not_twitter_lib import CheckMachine
from checklib import BaseChecker, Status, get_initialized_session
from checklib import rnd_username, rnd_password
from checklib import cquit
import secrets
import requests
import sys 
import urllib

class Checker(BaseChecker):
    def __init__(self, *args, **kwargs):
        super(Checker, self).__init__(*args, **kwargs)
        self.mch = CheckMachine(self)

    def action(self, action, *args, **kwargs):
        try:
            super(Checker, self).action(action, *args, **kwargs)
        except requests.exceptions.ConnectionError:
            self.cquit(Status.DOWN, 'Connection error', 'Got requests connection error')

    def check(self):
        login = secrets.token_hex(10)
        password = login
        s = requests.Session()
        #check register
        self.mch.register(s, login, password)
        #check login
        self.mch.login(s, login, password)
        #check upload by http link
        self.mch.check_upload_by_link(s, "http://example.com")
        self.cquit(Status.OK)
    
    def put(self, *_args, **_kwargs):
        raise NotImplementedError('You must implement this method')

    def get(self, flag_id, flag, vuln):
        self.cquit(Status.OK)

#for testing
c = Checker("95.182.120.116")
c.check()
"""
if __name__ == '__main__':
    c = Checker(sys.argv[2])

    try:
        c.action(sys.argv[1], *sys.argv[3:])
    except c.get_check_finished_exception():
        cquit(Status(c.status), c.public, c.private)
        """