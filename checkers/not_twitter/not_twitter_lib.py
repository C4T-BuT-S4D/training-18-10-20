import math
import random
from checklib import Status
import requests
import re
import urllib

PORT = 3113
MAX_FILESIZE = 1024

find_fileinfo_regexp = re.compile(r'<div class="filenames">(.*)</div>')
new_filename_link = re.compile(r'<div class="message">Ваш фанфик был загружен на (uploads/.*)</div>')


class CheckMachine:
    @property
    def url(self):
        return f'http://{self.c.host}:{self.port}'

    def __init__(self, checker):
        self.c = checker
        self.port = PORT
    
    def register(self, session, username, password, status=Status.MUMBLE):
        r = session.post(self.url + '/register', data = {'login':username, 'password': password})
        self.c.assert_eq(200, r.status_code, "Can't register", status=status)
        #print(r.status_code)

    def login(self, session, username, password, status=Status.MUMBLE):
        r = session.post(self.url + '/login', data = {'login':username, 'password': password})
        self.c.assert_eq(200, r.status_code, "Can't login", status=status)
        #print(r.status_code)
    
    def _upload_file_by_link(self, session, link, status=Status.MUMBLE):
        """
        return filename of uploaded file
        """
        #example_link = f"file:///services/not_twitter/uploads/{filename}"
        r = session.post(self.url + '/upload_by_link', data = {'link':link})
        self.c.assert_eq(200, r.status_code, "Can't upload file by link", status=status)
        new_link = new_filename_link.findall(r.text)[0]
        return new_link
    
    def upload_text(self, session, text, status=Status.MUMBLE):
        """
        return filename of uploaded file
        """
        r = session.post(self.url + '/upload', data = {'text':text})
        self.c.assert_eq(200, r.status_code, "Can't upload text", status=status)
        new_link = new_filename_link.findall(r.text)[0]
        return new_link

    
    def _download_file_by_link(self, session, link, status=Status.MUMBLE):
        """
        return file content
        """
        r = session.get(self.url + '/' + link)
        self.c.assert_eq(200, r.status_code, "Can't download file", status=status)
        return r.text
    
    def check_file_content_by_link(self, session, link, expected_content, status = Status.MUMBLE):
        file_content = self._download_file_by_link(session, link, status)
        self.c.assert_eq(file_content, expected_content, "Can't download text", status=status)
        #print(file_content == expected_content, file_content, expected_content)

    def check_upload_by_link(self, session, link, status=Status.MUMBLE):
        link_content = urllib.request.urlopen(link).read(MAX_FILESIZE).decode('utf-8')
        server_link = self._upload_file_by_link(session, link, status)
        link_content_on_server = self._download_file_by_link(session, server_link, status)
        self.c.assert_eq(link_content, link_content_on_server, "Can't upload file by link", status=status)
        #print(link_content_on_server == link_content)
        self._check_filename_in_uploads_page(session, server_link, status=status)
    
    def _get_uploads_list(self, s):
        limit = 128
        offset = 0
        uploads_html = s.get(self.url + f'/uploads?limit={limit}&offset={offset}').text
        files_info = find_fileinfo_regexp.findall(uploads_html)
        return[f"uploads/{x.split(': ')[0]}_{x.split(': ')[1]}" for x in files_info]

    def _check_filename_in_uploads_page(self, s, filename_link, status):
        uploads = self._get_uploads_list(s)
        #print(uploads, filename_link)
        #print(filename_link in uploads)
        self.c.assert_in(filename_link, uploads, "incorrect uploads", status=status)