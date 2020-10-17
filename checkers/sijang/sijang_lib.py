from pwn import *
from checklib import *

import random
import string

context.log_level = 'CRITICAL'

PORT = 9999

# global const
TCP_CONNECTION_TIMEOUT = 10
TCP_OPERATIONS_TIMEOUT = 10
alph = 'qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM0123456789'

class CheckMachine:
	sock = None
	_username = None

	def __init__( self, checker ):
		self.c = checker
		self.port = PORT

	def connection( self ):
		try:
			self.sock = remote( self.c.host, 
				self.port, 
				timeout = TCP_CONNECTION_TIMEOUT 
			)
			self.sock.settimeout( TCP_CONNECTION_TIMEOUT )
		except:
			self.sock = None
			self.c.cquit( Status.DOWN, 
				'Connection error',
				'CheckMachine.connection(): timeout connection!' 
			)

		self.sock.settimeout( TCP_OPERATIONS_TIMEOUT )

	def reg_user( self, username, password ):

		self.sock.recvuntil( b"> " ) # skip banner and menu
		self.sock.send( b"2\n" ) # send reg cmd
		self.sock.recvuntil( b": " ) # Enter username: 
		self.sock.send( username.encode() + b'\n' )

		buf = self.sock.recv()

		if b"User alredy exist" in buf:
			self.c.cquit( Status.MUMBLE, 
				"Can't register a new user!", 
				"User is already registered!" 
			)

		self.sock.send( password.encode() + b'\n' )
		data = self.sock.recvuntil( b"> " )

		if b"User menu:" not in data:
			self.c.cquit( Status.MUMBLE, 
				"Can't register a new user!", 
				"Registration process timeout!" 
			)

		return True

	def login( self, username, password ):

		self._username = username
		self.sock.recvuntil( b"> " )
		self.sock.send( b"1\n" )
		self.sock.recvuntil( b": " ) # Enter username: 
		self.sock.send( username.encode() + b'\n' )

		buf = self.sock.recv()

		if b"No such user!" in buf:
			return False, "{-} User not found!"

		self.sock.send( password.encode() + b'\n' )
		buf = self.sock.recvline()

		if b"Incorrect password" in buf:
			return False, "{-} Password is invalid!"

		return True, "OK"
		# except:
		# 	self.close_connect()
		# 	self.c.cquit( Status.MUMBLE, 
		# 		"Can't login by registered user!", 
		# 		"Login process timeout!" 
		# 	)

	def close_connect( self ):
		try:
			self.sock.close()
			self.sock = None
		except:
			self.sock = None

	def get_market_page( self ):
		self.sock.send( b"2\n" )

		data = self.sock.recvuntil( b"\n -- Buy Menu --" )
		self.sock.recvuntil( b"> " )
		self.sock.send( "4\n" )
		self.sock.recvuntil( b"> " )

		return data
		
	def sell_weapon( self, desc = None, archived = False ):
		# enter sell item option
		self.sock.send( b"3\n" )

		# enter weapon id
		self.sock.recvuntil( b"id: " )
		self.sock.send( b"0\n" )
		
		# accept selling
		self.sock.recvuntil( b"[y\\n]: " )
		self.sock.send( b"y\n" )
		
		# accept description
		self.sock.recvuntil( b"[y\\n]: " )
		
		if desc != None:
			self.sock.send( b"y\n" )
			self.sock.recvuntil( b"description: " )
			self.sock.send( desc.encode() + b"\n" )
		else:
			self.sock.send( b"n\n" )

		# enter description
		
		self.sock.recvuntil( b"weapon?[y\\n]: " )
		# accept archive
		if archived:
			self.sock.send( b"y\n" )
		else:
			self.sock.send( b"n\n" )

		data = self.sock.recv()

		while b"Item is " not in data:
		#data = self.sock.recvuntil( b"Item is " )
			data += self.sock.recv()

		if b"[+] Item is added" not in data:
			self.c.cquit( Status.MUMBLE, 
				"Can't add item to market",
				"Checker.sell_weapon(): out_data = {}".format( data )
			)

		while b"token" not in data:
			try:
				data += self.sock.recv()
			except:
				self.c.cquit( Status.MUMBLE, 
				"Can't get item token",
				"Checker.sell_weapon(): out_data = {}".format( data )
			)

		try:
			token = data.split( b'\n' )[-2]
			token = token.split( b": " )[1]
		except:
			self.c.cquit( Status.MUMBLE, 
				"Can't get item token",
				"Checker.sell_weapon(): out_data = {}".format( data )
			)

		self.sock.send( b"\n" )
		self.sock.recvuntil( b"> " )

		return token

	def sell_flag_weapon( self, flag ):
		# enter sell item option
		self.sock.send( b"3\n" )

		# enter weapon id
		self.sock.recvuntil( b"id: " )
		self.sock.send( b"0\n" )
		
		# accept selling
		self.sock.recvuntil( b"[y\\n]: " )
		self.sock.send( b"y\n" )
		
		# accept description			
		self.sock.recvuntil( b"[y\\n]: " )
		self.sock.send( b"y\n" )

		# enter description
		self.sock.recvuntil( b"description: " )
		self.sock.send( flag.encode() + b"\n" )

		# accept archive
		self.sock.recvuntil( b"weapon?[y\\n]: " )
		self.sock.send( b"y\n" )

		data = self.sock.recvuntil( b"Item is " )
		data += self.sock.recv()

		if b"[+] Item is added" not in data:
			self.c.cquit( Status.MUMBLE, 
				"Can't add item to market",
				"Checker.sell_flag_weapon(): out_data = {}".format( data )
			)

		while b"token" not in data:
			try:
				data += self.sock.recv()
			except:
				self.c.cquit( Status.MUMBLE, 
				"Can't get item token",
				"Checker.sell_flag_weapon(): out_data = {}".format( data )
			)
				
		try:
			token = data.split( b'\n' )[-2]
			token = token.split( b": " )[1]
		except:
			self.c.cquit( Status.MUMBLE, 
				"Can't get item token",
				"Checker.sell_flag_weapon(): out_data = {}".format( data )
			)

		self.sock.send( b"\n" )
		self.sock.recvuntil( b"> " )

		return token

	def get_archive_item( self, token ):
		self.sock.send( b"4\n" )
		self.sock.recvuntil( b"token: " )

		self.sock.send( token.encode() + b'\n' )
		data = self.sock.recvline()

		if b"not found!" in data:
			self.c.cquit( Status.CORRUPT, 
				"Can't find item by token!", 
				"Token of flag item is not founded, data ={}".format( data.decode() ) 
			)

		try:
			data = self.sock.recvuntil( b"status? [y\\n]: " )
			self.sock.send( b"n\n" ) 
			flag = data.split( b"\n" )[ 1 ].split( b": ")[ -1 ].decode()
			self.sock.recvuntil( b"> ")
		except:
			self.c.cquit( Status.CORRUPT, 
				"Can't get item token!", 
				"Token parse error, data ={}".format( data.decode() ) 
			)

		return flag

	def get_profile( self ):
		self.sock.send( b"1\n" )
		data = self.sock.recvuntil( b"\nUser menu:" )
		data = data.split( b"\n" )

		username = data[ 1 ][ 7 : -7 ]
		coins = int( data[ 2 ][ 8 : -2 ].decode(), 10 )
		weapon_set_status = data[ 3 ][ 18 : ]
		weapon_amount = int( data[ 4 ][ 18 : -2 ].decode(), 10 )
		weapon_list = []

		for i in range( 0, weapon_amount ):
			weapon_list.append( data[ 5 + i ][ 10: data[ 5 + i ].find( b", quality:" ) ] )

		profile = {'username':username, 'coins':coins, 
			'status':weapon_set_status, 'amount':weapon_amount,
			'weapons':weapon_list
		}

		self.sock.recvuntil( b"> " )
		return profile 

	def set_weapon( self ):
		self.sock.send( b"5\n" )

		self.sock.recvuntil( b"id: " )
		self.sock.send( "0\n" )

		data = self.sock.recvline()
		if b"[+] You set" not in data:
			self.cquit( Status.MUMBLE,
				"Can't set weapon",
				"Checker.set_weapon(): error in set , data = {}".format(data.encode())
			)

		self.sock.recvuntil( b"> " )

	def unset_weapon( self ):
		self.sock.send( b"6\n" )

		msg = self.sock.recvline()

		if b"[+] Weapon removed!" not in msg:
			self.cquit( Status.MUMBLE,
				"Can't unset weapon",
				"Checker.unset_weapon(): error in banner, data = {}".format(msg.encode())
			)

		self.sock.recvuntil( b"> " )

	def safe_close_connection( self ):
		#self.sock.recvuntil( b"> " )
		self.sock.send( "7\n" )

		self.sock.recvuntil( b"> " )
		self.sock.send( "3\n" )
		
		self.sock.close()
		self.sock = None
