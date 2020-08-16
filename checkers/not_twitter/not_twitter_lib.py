import math
import random
from checklib import Status
import requests
import re
import urllib

PORT = 3113
MAX_FILESIZE = 1024

find_fileinfo_regexp = re.compile(r'<div class="filenames">(.*)</div>')
new_filename_link = re.compile(r"your file uploaded to '(.*)'")



class CheckMachine:
    @property
    def url(self):
        #return f'http://{self.c.host}:{self.port}'
        #change it before game
        return "http://95.182.120.116:3113"

    def __init__(self, checker):
        self.c = checker
        self.port = PORT
    
    def register(self, session, username, password, status=Status.MUMBLE):
        r = session.post(self.url + '/register', data = {'login':username, 'password': password})
        #self.c.assert_eq(200, r.status_code, "Can't register")
        print(r.status_code)

    def login(self, session, username, password, status=Status.MUMBLE):
        r = session.post(self.url + '/login', data = {'login':username, 'password': password})
        #self.c.assert_eq(200, r.status_code, "Can't login")
        print(r.status_code)
    
    def _upload_file_by_link(self, session, link):
        """
        return filename of uploaded file
        """
        #example_link = f"file:///services/not_twitter/uploads/{filename}"
        r = session.post(self.url + '/upload_by_link', data = {'link':link})
        new_link = new_filename_link.findall(r.text)[0]
        return new_link
    
    def upload_text(self, session, text):
        """
        return filename of uploaded file
        """
        #example_link = f"file:///services/not_twitter/uploads/{filename}"
        r = session.post(self.url + '/upload', data = {'text':text})
        new_link = new_filename_link.findall(r.text)[0]
        return new_link

    
    def _download_file_by_link(self, session, link):
        """
        return file content
        """
        return session.get(self.url + '/' + link).text
    
    def check_file_content_by_link(self, session, link, expected_content, status = Status.MUMBLE):
        file_content = self._download_file_by_link(session, link)
        #self.c.assert_eq(file_content, expected_content, "Can't upload text", status=status)
        print(file_content == expected_content, file_content, expected_content)

    def check_upload_by_link(self, session, link, status=Status.MUMBLE):
        link_content = urllib.request.urlopen(link).read(MAX_FILESIZE).decode('utf-8')
        server_link = self._upload_file_by_link(session, link)
        link_content_on_server = self._download_file_by_link(session, server_link)
        #self.c.assert_eq(link_content, link_content_on_server, "Can't upload file by link")
        print(link_content_on_server == link_content)