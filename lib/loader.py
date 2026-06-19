import re
from .utils import note, to_lowercase, canonicalize, del_inline_comment

max_call_adr = 0x3ffff

commands = {}
datalabels = {}
disas_filename = None
result = []
labels = {}
address_requests = []
relocation_expressions = []
sizeof_cmds = []
deferred_evals = []
home = None
in_comment = False
vars_dict = {}
current_section_name = None
disasm = []

def add_command(command_dict, address, command, tags, debug_info=''):
    ''' Add a command to command_dict. '''
    assert command, f'Empty command {debug_info}'
    assert type(command_dict) is dict

    for disallowed_prefix in '0x', 'call', 'goto':
        assert not command.startswith(disallowed_prefix), \
            f'Command ends with "{disallowed_prefix}" {debug_info}'
    assert not command.endswith(':'), \
        f'Command ends with ":" {debug_info}'
    assert ';' not in command, \
        f'Command contains ";" {debug_info}'

    for prev_command, (prev_adr, prev_tags) in command_dict.items():
        if prev_command == command:
            if prev_adr == address and prev_tags == tuple(tags):
                return
            assert False, f'Command appears twice - ' \
                f'first: {prev_command} -> {prev_adr:05X} {prev_tags}, ' \
                f'second: {command} -> {address:05X} {tags} - ' \
                f'{debug_info}'

    command_dict[command] = (address, tuple(tags))

def get_commands(gadgets_file, labels_file):
    ''' Read a list of gadget names and parse a rename list. '''
    global commands, datalabels
    
    # 1. Parse gadgets file
    with open(gadgets_file, 'r', encoding='utf-8') as f:
        data = f.read().splitlines()

    in_comment = False
    line_regex = re.compile(r'([0-9a-fA-F]+)\s+(.+)')
    for line_index0, line in enumerate(data):
        line = line.strip()

        if line == '/*':
            in_comment = True
            continue
        if line == '*/':
            in_comment = False
            continue
        if in_comment:
            continue

        line = del_inline_comment(line)
        if not line:
            continue

        match = line_regex.fullmatch(line)
        if not match:
            continue
        address, command = match[1], match[2]

        command = canonicalize(command)
        command = to_lowercase(command)

        tags = []
        while command and command[0] == '{':
            i = command.find('}')
            if i < 0:
                raise Exception(f'Line {line_index0 + 1} '
                                'has unmatched "{"')
            tags.append(command[1:i])
            command = command[i + 1:]

        try:
            address = int(address, 16)
        except ValueError:
            raise Exception(f'Line {line_index0 + 1} has invalid address: {address!r}')

        add_command(commands, address, command, tags, f'at {gadgets_file}:{line_index0 + 1}')

    # 2. Parse labels file (rename list)
    with open(labels_file, 'r', encoding='u8') as f:
        data = f.read().splitlines()

    line_regex_rename = re.compile(r'^\s*([\w_.]+)\s+([\w_.]+)')
    global_regex = re.compile(r'f_([0-9a-fA-F]+)')
    local_regex  = re.compile(r'.l_([0-9a-fA-F]+)')
    data_regex   = re.compile(r'd_([0-9a-fA-F]+)')
    hexadecimal  = re.compile(r'[0-9a-fA-F]+')

    last_global_label = None
    for line_index0, line in enumerate(data):
        match = line_regex_rename.match(line)
        if not match: continue
        raw, real = match[1], match[2]
        if real.startswith('.'):
            continue
        
        match = data_regex.fullmatch(raw)
        if match:
            addr = int(match[1], 16)
            datalabels[real] = addr
            continue

        addr = None
        if hexadecimal.fullmatch(raw):
            addr = int(raw, 16)
            last_global_label = None
        else:
            match = global_regex.match(raw)
            if match:
                addr = int(match[1], 16)
                if len(match[0]) == len(raw):
                    last_global_label = addr
                else:
                    match = local_regex.fullmatch(raw[len(match[0]):])
                    if match:
                        addr += int(match[1], 16)
            else:
                match = local_regex.fullmatch(raw)
                if match:
                    if last_global_label is None:
                        print('Label cannot be read: ', line)
                        continue
                    else:
                        addr = last_global_label + int(match[1], 16)

        if addr is not None:
            assert addr < len(disasm), f'{addr:05X}'
            if disasm[addr].startswith('push lr'):
                tags = 'del lr',
                addr += 2
            else:
                tags = 'rt',
                a1 = addr + 2
                while not any(disasm[a1].startswith(x) for x in ('push lr', 'pop pc', 'rt')): a1 += 2
                if not disasm[a1].startswith('rt'):
                    tags = tags + ('del lr',)

            if real in commands:
                if 'override rename list' in commands[real][1]:
                    continue
                if commands[real] == (addr, tags):
                    note(f'Warning: Duplicated command {real}\n')
                    continue

            add_command(commands, addr, real, tags=tags,
                    debug_info=f'at {labels_file}:{line_index0+1}')
        else:
            raise ValueError('Invalid line: ' + repr(line))

def get_disassembly(filename):
    '''Try to parse a disasm file with annotated address.

    Each line should look like this:

        mov r2, 1                      ; 0A0A2 | 0201
    '''
    global disasm
    with open(filename, 'r', encoding='u8') as f:
        data = f.read().splitlines()

    # Pre-allocate array of strings to avoid resizing/appending overhead
    disasm = [''] * 262144
    for line in data:
        if line.startswith('\t') and ';' in line:
            parts = line.split(';', 1)
            instr = parts[0].strip()
            comment = parts[1]
            if '|' in comment:
                addr_hex = comment.split('|', 1)[0].strip()
                try:
                    addr = int(addr_hex, 16)
                    disasm[addr] = instr
                except ValueError:
                    pass

def sizeof_register(reg_name):
    return {'r': 1, 'e': 2, 'x': 4, 'q': 8}[reg_name[0]]
