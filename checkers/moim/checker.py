#!/usr/bin/env python3
import tempfile

from gevent import monkey, sleep

monkey.patch_all()

import sys
import textract
from random import randint, choice
import checklib
from faker import Faker

from moim_lib import *

anime_img_urls = [
    'https://i.pinimg.com/236x/ce/17/c4/ce17c464f0680d0490752781d7c002be.jpg',
    'https://i.ytimg.com/vi/wIdsuaupKoA/maxresdefault.jpg',
    'https://images1.myreviewer.co.uk/medium/0000214025.jpg',
    'https://thereviewmonster.files.wordpress.com/2019/01/nina.jpg',
    'https://i.ytimg.com/vi/LZIgyrSvDbk/hqdefault.jpg',
    'https://www.overthinkingit.com/wp-content/uploads/2009/12/Spike-Takes-a-Dump-590x448.jpg',
]


class Checker(BaseChecker):
    uses_attack_data = True
    timeout = 15

    def __init__(self, *args, **kwargs):
        super(Checker, self).__init__(*args, **kwargs)
        self.mch = CheckMachine(self)
        self.f = Faker()

    def get_images(self):
        images_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'images')
        return [os.path.join(images_dir, x) for x in os.listdir(images_dir) if not x.startswith('.')]

    def remap(self, l, key='id'):
        d = {}
        for v in l:
            d[v[key]] = v
        return d

    def extract_text(self, file_resp):
        try:
            ntf = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
            ntf.write(file_resp.content)
            ntf.close()
            data = textract.process(ntf.name, encoding='utf-8')
            os.unlink(ntf.name)
        except Exception:
            return b''
        return data

    def create_meeting_with_image(self, desc, sess, title, capacity):
        params = {'height': f'{randint(20, 60)}%', 'width': f'{randint(20, 60)}%'}
        image_file = None
        image_url = None
        if randint(0, 1) == 0:
            image_file = open(choice(self.get_images()), 'rb')
        else:
            image_url = choice(anime_img_urls)
        meeting_data = self.mch.create_meeting(sess, title=title, desc=desc, capacity=capacity, image_file=image_file,
                                               image_url=image_url, image_params=params)
        return meeting_data

    def check_ticket_content(self, flag, ticket_data_resp):
        self.assert_eq(ticket_data_resp.headers.get('Content-Type'), 'application/pdf', 'Failed to download ticket',
                       status=Status.MUMBLE)
        self.assert_gt(int(ticket_data_resp.headers.get('Content-Length', 0)), 0, 'Failed to download ticket',
                       status=Status.MUMBLE)
        self.assert_in(flag.encode(), self.extract_text(ticket_data_resp), 'Failed to read ticket data',
                       status=Status.MUMBLE,
                       )

    def check_response(self, r: requests.Response, public: str, status=checklib.status.Status.MUMBLE):
        try:
            error = r.json()['error']
        except Exception as e:
            error = r.text[:50]
        if r.status_code >= 500:
            self.cquit(status, public, f'Code {r.status_code} on {r.url}, error = {error}')
        if not r.ok:
            self.cquit(status, public, f'Error on {r.url}: {r.status_code}, error = {error}')

    def action(self, action, *args, **kwargs):
        try:
            super(Checker, self).action(action, *args, **kwargs)
        except requests.exceptions.ConnectionError:
            self.cquit(Status.DOWN, 'Connection error', 'Got requests connection error')

    def check(self):
        u, p, _ = self.mch.register_user()
        sess = self.mch.login_user(u, p)

        title = self.f.sentence(nb_words=1)
        desc = self.f.sentence(nb_words=3)

        capacity = randint(3, 10)
        meeting_data = self.create_meeting_with_image(desc, sess, title, capacity)
        meeting_id = meeting_data.get('id')

        meetings_data = self.mch.list_meetings(sess)
        meetings_data = self.remap(meetings_data).get(int(meeting_id))

        self.assert_neq(meetings_data, None, 'Failed to get user syncs', status=Status.MUMBLE)
        self.assert_eq(meetings_data.get('title'), title, 'Failed to get user syncs', status=Status.MUMBLE)
        self.assert_eq(meetings_data.get('description'), desc, 'Failed to get user syncs', status=Status.MUMBLE)

        _, _, client_sess = self.mch.register_user()

        sync_info = self.mch.get_sync_info(client_sess, meeting_id)
        self.assert_eq(sync_info.get('author', dict()).get('email'), u, 'Failed to get sync info', status=Status.MUMBLE)
        self.assert_gt(sync_info.get('capacity', 0), 0, 'Sync capacity is reached', status=Status.MUMBLE)
        fake_flag = rnd_username()
        member_data = self.mch.add_member(client_sess, meeting_id, fake_flag)

        public_id = member_data.get('public_id')
        self.assert_neq(public_id, None, 'Failed to add sync member', status=Status.MUMBLE)

        for _ in range(5):
            sleep(0.5)
            ticket_info = self.mch.get_ticket_data(client_sess, public_id)
            self.assert_eq(ticket_info.get('nickname'), fake_flag, 'Failed to get ticket data', status=Status.MUMBLE)
            if ticket_info.get('ticket_url'):
                ticket_data_resp = self.mch.get_ticket(client_sess, ticket_info.get('ticket_url'))
                self.check_ticket_content(fake_flag, ticket_data_resp)
                break

        members_data = self.mch.list_members(sess, meeting_id)
        member = self.remap(members_data, key='public_id').get(public_id)
        self.assert_neq(member, None, 'Failed to get sync members', status=Status.MUMBLE)
        self.assert_eq(member.get('nickname'), fake_flag, 'Failed to get sync members', status=Status.MUMBLE)

        self.cquit(Status.OK)

    def put(self, flag_id, flag, vuln):
        u, p, _ = self.mch.register_user()
        sess = self.mch.login_user(u, p)

        title = self.f.sentence(nb_words=1)
        desc = self.f.sentence(nb_words=3)
        meeting_data = self.create_meeting_with_image(desc, sess, title, capacity=3)
        cu, cp, client_sess = self.mch.register_user()
        meeting_id = meeting_data.get('id')
        member_data = self.mch.add_member(client_sess, meeting_id, flag)
        public_id = member_data.get('public_id')
        self.assert_neq(public_id, None, 'Failed to add member', status=Status.MUMBLE)
        full_data = {
            'u': u,
            'p': p,
            'public_id': public_id,
            'm_id': meeting_id,
            'cu': cu,
            'cp': cp,
        }
        self.cquit(Status.OK, f'sync_{meeting_id}', json.dumps(full_data))

    def get(self, flag_id, flag, vuln):
        data = json.loads(flag_id)
        u, p = data['u'], data['p']
        sess = self.mch.login_user(u, p)
        self.mch.list_members(sess, data['m_id'])
        members_data = self.mch.list_members(sess, data['m_id'])
        member = self.remap(members_data, key='public_id').get(data['public_id'])
        self.assert_neq(member, None, 'Failed to get sync members', status=Status.CORRUPT)
        self.assert_eq(member.get('nickname'), flag, 'Failed to get sync members', status=Status.CORRUPT)

        client_sess = self.mch.login_user(data['cu'], data['cp'])

        for _ in range(20):
            sleep(0.5)
            ticket_data = self.mch.get_ticket_data(client_sess, data['public_id'])
            self.assert_eq(ticket_data.get('nickname'), flag, 'Failed to get ticket data', status=Status.CORRUPT)
            if ticket_data.get('ticket_url'):
                ticket_data_resp = self.mch.get_ticket(client_sess, ticket_data.get('ticket_url'))
                self.check_ticket_content(flag, ticket_data_resp)
                break
        else:
            self.cquit(Status.CORRUPT, 'Failed to read ticket content')
        self.cquit(Status.OK)


if __name__ == '__main__':
    c = Checker(sys.argv[2])

    try:
        c.action(sys.argv[1], *sys.argv[3:])
    except c.get_check_finished_exception():
        cquit(Status(c.status), c.public, c.private)
