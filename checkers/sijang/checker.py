#!/usr/bin/env python3

from gevent import monkey

monkey.patch_all()

import sys
import os
import string
import random
import copy

from checklib import *

argv = copy.deepcopy( sys.argv )
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sijang_lib import *

# my utils
def idg( size = 8, chars = alph ):
	return ''.join( random.choice( chars ) for _ in range( size ) )

class Checker(BaseChecker):
	uses_attack_data = True
	timeout = 15  # 15 seconds
	vulns = 1  # 1 places for flags

	def __init__(self, *args, **kwargs):	
		super(Checker, self).__init__(*args, **kwargs)
		self.mch = CheckMachine(self)

	def action(self, action, *args, **kwargs):
		super( Checker, self ).action( action, *args, **kwargs )

	def check( self ):
		self.mch.connection()

		# check register and login
		username = idg()
		password = idg()

		self.mch.reg_user( username, password )
		
		# set weapon and check
		profile = self.mch.get_profile()
		
		if len( profile[ 'weapons' ] ) < 1:
			self.cquit( Status.MUMBLE,
				"User has no weapon!",
				"Checker.check(): user has no weapon!"
			)

		self.mch.set_weapon()
		tmp_profile = self.mch.get_profile()

		user_weapon = profile[ 'weapons' ][ 0 ]

		if profile[ 'weapons' ][ 0 ] != tmp_profile[ 'status' ]:
			self.cquit( Status.MUMBLE,
				"Can't set weapon",
				"Checker.check(): error in set"
			)

		# unset weapon and check
		self.mch.unset_weapon()
		profile = self.mch.get_profile()

		if profile[ 'status' ] != b"not set" or profile[ 'weapons' ][ 0 ] != tmp_profile[ 'status' ]:
			self.cquit( Status.MUMBLE,
				"Can't unset weapon",
				"Checker.check(): error in unset"
			)

		# sell weapon and check
		description = idg()
		token = self.mch.sell_weapon( description )

		# buy weapon, find our weapon
		data = self.mch.get_market_page()

		if not user_weapon in data:
			self.cquit( Status.MUMBLE,
				"Can't find selled weapon in market page",
				"Checker.check(): weapon is not on market page!"
			)

		# sell archived weapon, change status

		self.mch.safe_close_connection()
		self.cquit( Status.OK )

	def put( self, flag_id, flag, vuln ):

		self.mch.connection()
		
		username = idg()
		password = idg()

		self.mch.reg_user( username, password )

		item_token = self.mch.sell_flag_weapon( flag ).decode()
		self.mch.safe_close_connection()

		self.cquit( Status.OK, f'{item_token}', f'{username}:{password}:{item_token}' ) 

	def get( self, flag_id, flag, vuln ):
		username, password, token = flag_id.split( ":" )

		self.mch.connection()
		logined, err_msg = self.mch.login( username, password )

		if not logined:
			self.cquit( Status.CORRUPT,
				"Can't login and flag check!",
				"Checker.login(): err_msg = {}".format( err_msg ) 
			)

		u_flag = self.mch.get_archive_item( token )

		if u_flag != flag:
			self.cquit( Status.CORRUPT,
				"Incorrect flag",
				"Checker.get_status(): valid_flag = {}, user_flag = {}".format(
					flag, status )
			)

		self.mch.safe_close_connection()
		self.cquit( Status.OK )

if __name__ == '__main__':
	c = Checker(argv[2])

	try:
		c.action(argv[1], *argv[3:])
	except c.get_check_finished_exception():
		cquit(Status(c.status), c.public, c.private)