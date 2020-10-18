from copy import copy
from random import randint, choices, choice, shuffle

from fixedint import MutableInt64

def copysign(a, b):
    if b == 0:
        return 0
    return abs(a) * b // abs(b)

def generate_number(registers, register, temp_register, target_value):
    registers = copy(registers)
    operations = ['m', 'i', 'd', '+', '-', '*', '/', '&', '|', '^', '~', 'B']

    code = ""

    junk = choices(operations, k=randint(10, 20))
    for op in junk:
        if op == 'm':
            to = choice([register, temp_register])
            fr = choice([register, temp_register])
            code += f"{op}{to}{fr}"
            registers[to] = MutableInt64(int(registers[fr]))
        elif op == 'i':
            tg = choice([register, temp_register])
            code += f"{op}{tg}"
            registers[tg] += 1
        elif op == 'd':
            tg = choice([register, temp_register])
            code += f"{op}{tg}"
            registers[tg] -= 1
        elif op == '+':
            to = choice([register, temp_register])
            fr = choice([register, temp_register])
            code += f"{op}{to}{fr}"
            registers[to] += registers[fr]
        elif op == '-':
            to = choice([register, temp_register])
            fr = choice([register, temp_register])
            code += f"{op}{to}{fr}"
            registers[to] -= registers[fr]
        elif op == '*':
            to = choice([register, temp_register])
            fr = choice([register, temp_register])
            code += f"{op}{to}{fr}"
            registers[to] *= registers[fr]
        elif op == '/':
            to = choice([register, temp_register])
            fr = choice([register, temp_register])
            if registers[fr] == 0:
                code += f"i{fr}"
                registers[fr] += 1
            code += f"{op}{to}{fr}"
            registers[to] = MutableInt64(copysign(abs(int(registers[to])) // abs(int(registers[fr])), int(registers[to]) * int(registers[fr])))
        elif op == '&':
            to = choice([register, temp_register])
            fr = choice([register, temp_register])
            code += f"{op}{to}{fr}"
            registers[to] &= registers[fr]
        elif op == '|':
            to = choice([register, temp_register])
            fr = choice([register, temp_register])
            code += f"{op}{to}{fr}"
            registers[to] |= registers[fr]
        elif op == '^':
            to = choice([register, temp_register])
            fr = choice([register, temp_register])
            code += f"{op}{to}{fr}"
            registers[to] ^= registers[fr]
        elif op == '~':
            tg = choice([register, temp_register])
            code += f"{op}{tg}"
            registers[tg] = ~registers[tg]
        elif op == 'B':
            tg = choice([register, temp_register])
            code += f"B{tg}^{tg}{tg}"
            registers[tg] *= 0

    if abs(registers[register] - target_value) > 300:
        code += f"m{register}{temp_register}"
        registers[register] = MutableInt64(int(registers[temp_register]))
        if registers[temp_register] == 0:
            code += f"i{register}i{temp_register}"
            registers[register] += 1
            registers[temp_register] += 1
        code += f"/{register}{temp_register}"
        registers[register] = MutableInt64(copysign(abs(int(registers[register])) // abs(int(registers[temp_register])),
                                           int(registers[register]) * int(registers[temp_register])))

    while registers[register] < target_value:
        code += f"i{register}"
        registers[register] += 1

    while registers[register] > target_value:
        code += f"d{register}"
        registers[register] -= 1

    return registers, code


def generate_string(registers, register, temp_register, target_string, use_temp=True):
    code = ""
    for c in target_string:
        i_register = choice(['r', 'j', 'q', 'l'])
        i_register_temp = choice(list({'r', 'j', 'q', 'l'} - {i_register}))
        registers, ca = generate_number(registers, i_register, i_register_temp, ord(c))
        code += ca
        if not use_temp or randint(0, 1) == 0:
            code += f"a{register}{i_register}"
            registers[register] += chr(registers[i_register])
        else:
            code += f"M{temp_register}{register}a{temp_register}{i_register}M{register}{temp_register}"
            registers[temp_register] = registers[register]
            registers[temp_register] += chr(registers[i_register])
            registers[register] = registers[temp_register]

    return registers, code


def generate_frames_from_string(registers, register1, register2, target_string):
    l = len(target_string) // 2
    str1 = target_string[:l]
    str2 = target_string[l:]

    code = ""

    registers, ca = generate_string(registers, register1, "", str1, False)
    code += ca

    registers, ca = generate_string(registers, register2, "", str2, False)
    code += ca

    return registers, code


def generate_write_to_file(registers, target_filename, target_string):
    code = ""

    registers_order = ['o', 't', 'd']
    shuffle(registers_order)

    registers, ca = generate_string(registers, registers_order[0], registers_order[1], target_filename)
    code += ca

    code += f"M{registers_order[1]}{registers_order[2]}"
    registers[registers_order[1]] = registers[registers_order[2]]

    i_register = choice(['r', 'j', 'q', 'l'])
    i_register_temp = choice(list({'r', 'j', 'q', 'l'} - {i_register}))
    registers, ca = generate_number(registers, i_register, i_register_temp, 0)
    code += ca

    i_register2 = choice(list({'r', 'j', 'q', 'l'} - {i_register, i_register_temp}))
    i_register_temp2 = choice(list({'r', 'j', 'q', 'l'} - {i_register, i_register_temp, i_register2}))
    registers, ca = generate_number(registers, i_register2, i_register_temp2, 1)
    code += ca

    registers, ca = generate_number(registers, i_register_temp, i_register_temp2, 6)
    code += ca

    code += f"c{i_register2}#J{i_register}{i_register2}{i_register_temp}j{i_register}c{i_register_temp}#0#0#0#0#"

    registers, ca = generate_frames_from_string(registers, registers_order[1], registers_order[2], target_string)
    code += ca

    code += f"o{registers_order[0]}ww{registers_order[1]}w{registers_order[2]}"

    return registers, code


def generate_read_from_file(registers, target_filename, target_cnt):
    code = ""

    registers_order = ['o', 't', 'd']
    shuffle(registers_order)

    registers, ca = generate_string(registers, registers_order[0], registers_order[1], target_filename)
    code += ca

    code += f"M{registers_order[1]}{registers_order[2]}"
    registers[registers_order[1]] = registers[registers_order[2]]

    i_register = choice(['r', 'j', 'q', 'l'])
    i_register_temp = choice(list({'r', 'j', 'q', 'l'} - {i_register}))
    registers, ca = generate_number(registers, i_register, i_register_temp, 0)
    code += ca

    i_register2 = choice(list({'r', 'j', 'q', 'l'} - {i_register, i_register_temp}))
    i_register_temp2 = choice(list({'r', 'j', 'q', 'l'} - {i_register, i_register_temp, i_register2}))
    registers, ca = generate_number(registers, i_register2, i_register_temp2, 1)
    code += ca

    registers, ca = generate_number(registers, i_register_temp, i_register_temp2, 6)
    code += ca

    code += f"c{i_register2}#J{i_register}{i_register2}{i_register_temp}j{i_register}c{i_register_temp}#0#0#0#0#"

    registers, ca = generate_number(registers, i_register, i_register_temp, target_cnt)
    code += ca

    code += f"o{registers_order[0]}rr{registers_order[1]}{i_register}!{registers_order[1]}"

    return registers, code


def write_to_file(filename, string):
    registers = {
        'r': MutableInt64(0),
        'j': MutableInt64(0),
        'q': MutableInt64(0),
        'l': MutableInt64(0),
        'o': '',
        't': '',
        'd': ''
    }
    return generate_write_to_file(registers, filename, string)[1]


def read_from_file(filename, cnt):
    registers = {
        'r': MutableInt64(0),
        'j': MutableInt64(0),
        'q': MutableInt64(0),
        'l': MutableInt64(0),
        'o': '',
        't': '',
        'd': ''
    }
    return generate_read_from_file(registers, filename, cnt)[1]
