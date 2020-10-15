#!/usr/bin/env python3

from gevent import monkey

monkey.patch_all()

import sys
import requests
from checklib import *
from sumgyeojin_lib import CheckMachine
from generate_bytecode import write_to_file, read_from_file

class Checker(BaseChecker):
    def __init__(self, *args, **kwargs):
        uses_attack_data = False
        timeout = 15
        vulns = 1
        super(Checker, self).__init__(*args, **kwargs)
        self.mch = CheckMachine(self)

    def action(self, action, *args, **kwargs):
        try:
            super(Checker, self).action(action, *args, **kwargs)
        except requests.exceptions.ConnectionError:
            self.cquit(Status.DOWN, 'Connection error', 'Got requests connection error')

    def check(self):
        s = self.get_initialized_session()
        flag_filename = f"flag_{rnd_string(20)}"
        rs = rnd_string(32)

        bc = write_to_file(f"/jail/{flag_filename}", rs)
        vmid = self.mch.create_vm(s, bc)
        bc = self.mch.get_vm(s, vmid)
        self.mch.run_write_to_file(s, bc, flag_filename, rs)

        bc = read_from_file(f"/jail/{flag_filename}", len(rs))
        vmid = self.mch.create_vm(s, bc)
        bc = self.mch.get_vm(s, vmid)
        self.mch.run_read_from_file(s, bc, flag_filename, rs)

        self.cquit(Status.OK)

    def put(self, flag_id, flag, vuln):
        s = self.get_initialized_session()
        flag_filename = f"flag_{rnd_string(20)}"
        bc = write_to_file(f"/jail/{flag_filename}", flag)
        vmid = self.mch.create_vm(s, bc)
        bc = self.mch.get_vm(s, vmid, Status.CORRUPT)

        self.mch.run_write_to_file(s, bc, flag_filename, flag, Status.CORRUPT)

        self.cquit(Status.OK, flag_filename)

    def get(self, flag_id, flag, vuln):
        s = self.get_initialized_session()
        flag_filename = flag_id

        bc = read_from_file(f"/jail/{flag_filename}", len(flag))
        vmid = self.mch.create_vm(s, bc)
        bc = self.mch.get_vm(s, vmid, Status.CORRUPT)

        self.mch.run_read_from_file(s, bc, flag_filename, flag, Status.CORRUPT)

        self.cquit(Status.OK)

if __name__ == '__main__':
    c = Checker(sys.argv[2])

    try:
        c.action(sys.argv[1], *sys.argv[3:])
    except c.get_check_finished_exception():
        cquit(Status(c.status), c.public, c.private)
