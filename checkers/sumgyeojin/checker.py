#!/usr/bin/env python3

from gevent import monkey

monkey.patch_all()

import sys
import json
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
		super(Checker, self).action(action, *args, **kwargs)

	def check(self):
		s = get_initialized_session()
		rs = rnd_string(20)
		flag_filename = f"/flag_{rnd_string(20)}"

		bc = write_to_file(flag_filename, rs)
		vmid = self.mch.create_vm(s, bc)
		bc = self.mch.get_vm(s, vmid)

		self.mch.run_write_to_file(bc, flag_filename, rs)

		self.cquit(Status.OK)

	def put(self, flag_id, flag, vuln):
		s = get_initialized_session()
		flag_filename = f"/flag_{rnd_string(20)}"
		bc = write_to_file(flag_filename, flag)
		vmid = self.mch.create_vm(s, bc)
		self.cquit(Status.OK, json.dumps({
			"vmid": vmid,
			"flag_filename": flag_filename
		}))

	def get(self, flag_id, flag, vuln):
		self.cquit(Status.OK)

if __name__ == '__main__':
	c = Checker(sys.argv[2])

	try:
		c.action(sys.argv[1], *sys.argv[3:])
	except c.get_check_finished_exception():
		cquit(Status(c.status), c.public, c.private)
