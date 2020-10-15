#!/usr/bin/env python3

from gevent import monkey
monkey.patch_all()

from not_twitter_lib import CheckMachine
from checklib import BaseChecker, Status, get_initialized_session
from checklib import rnd_username, rnd_password
from checklib import cquit
import secrets
import requests
import sys 
import urllib


class Checker(BaseChecker):
    uses_attack_data = True

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
        password = secrets.token_hex(10)
        s = get_initialized_session()
        #check register
        self.mch.register(s, login, password)
        #check login
        self.mch.login(s, login, password)
        #check upload by http link (+ get this file ; + it appears in uploads)
        #self.mch.check_upload_by_link(s, "http://example.com")
        self.mch.check_upload_by_link(s, "http://example.com", login)
        self.cquit(Status.OK)
    
    def put(self, flag_id, flag, vuln):
        login = secrets.token_hex(10)
        password = secrets.token_hex(10)
        s = get_initialized_session()
        self.mch.register(s, login, password)
        self.mch.login(s, login, password)
        link = self.mch.upload_text(s, flag)
        self.cquit(Status.OK, f'{login}', f'{login}:{password}:{link}')

    def get(self, flag_id, flag, vuln):
        s = get_initialized_session()
        u, p, link = flag_id.split(':')
        self.mch.login(s, u, p, Status.CORRUPT)
        self.mch.check_file_content_by_link(s, link, flag, Status.CORRUPT)
        self.cquit(Status.OK)


if __name__ == '__main__':
    c = Checker(sys.argv[2])

    try:
        c.action(sys.argv[1], *sys.argv[3:])
    except c.get_check_finished_exception():
        cquit(Status(c.status), c.public, c.private)
