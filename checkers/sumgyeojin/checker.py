#!/usr/bin/env python3

from gevent import monkey

monkey.patch_all()

import sys
from checklib import *
from sumgyeojin_lib import CheckMachine

class Checker(BaseChecker):
	def __init__(self, *args, **kwargs):
		uses_attack_data = True
		timeout = 15
		vulns = 1
		super(Checker, self).__init__(*args, **kwargs)
		self.mch = CheckMachine(self)

	def action(self, action, *args, **kwargs):
		super(Checker, self).action(action, *args, **kwargs)

	def check(self):
		self.cquit(Status.OK)

	def put(self, flag_id, flag, vuln):
		self.cquit(Status.OK, f'', f'')

	def get(self, flag_id, flag, vuln):
		self.cquit(Status.OK)

if __name__ == '__main__':
	c = Checker(sys.argv[2])

	try:
		c.action(sys.argv[1], *sys.argv[3:])
	except c.get_check_finished_exception():
		cquit(Status(c.status), c.public, c.private)
