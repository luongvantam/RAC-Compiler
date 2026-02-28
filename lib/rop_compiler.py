# -*- coding: utf-8 -*-
# Created by user202729
# Modified by hieuxyz(comment,supported by casio2k9) (HD Compiler), luongvantam (RAC Compiler)
from ast import expr
import re, sys, os
from functools import lru_cache
from lib.text import char_to_hex
from lib.find_gadgets import find_first_gadget

max_call_adr = 0x3ffff

PYTHON_FUNCTIONS = {}
class PyNamespace:
    def __init__(self, functions):
        for name, func in functions.items():
            setattr(self, name, func)
    def __getattr__(self, name):
        raise AttributeError(f"Python function '{name}' not found")

def set_font(font_):
    global font, font_assoc
    font = font_
    font_assoc = dict((c, i) for i, c in enumerate(font))

def from_font(st):
    return [font_assoc[char] for char in st]

def to_font(charcodes):
    return ''.join(font[charcode] for charcode in charcodes)

def set_npress_array(npress_):
    global npress
    npress = npress_

def set_symbolrepr(symbolrepr_):
    global symbolrepr
    symbolrepr = symbolrepr_

@lru_cache(maxsize=256)
def byte_to_key(byte):
    if byte == 0:
        return '<NUL>'

    # TODO hack for classwiz without unstable
    sym = symbolrepr[byte]
    return f'<{byte:02x}>' if sym in ('@', '') else sym

    offset = 0
    sym = symbolrepr[byte]
    while byte and npress[byte] >= 100:
        byte = byte - 1
        offset += 1
    typesym = symbolrepr[byte] if byte else 'NUL'

    if set(sym) & set('\'"<>:'):
        sym = repr(sym)
    if set(typesym) & set('\'"<>:+'):
        typesym = repr(typesym)

    if offset == 0:
        return sym
    else:
        return f'<{sym}:{typesym}+{offset}>'

def get_npress(charcodes):
    if isinstance(charcodes, int):
        charcodes = (charcodes,)
    return sum(npress[charcode] for charcode in charcodes)

def get_npress_adr(adrs):
    if isinstance(adrs, int):
        adrs = (adrs,)
    assert all(0 <= adr <= max_call_adr for adr in adrs)
    return sum(get_npress((adr & 0xFF, (adr >> 8) & 0xFF)) for adr in adrs)

def optimize_adr_for_npress(adr):
    '''
    For a 'POP PC' command, the lowest significant bit in the address
    does not matter. This function use that fact to minimize number
    of key strokes used to enter the hackstring.
    '''
    return min((adr, adr ^ 1), key=get_npress_adr)

def optimize_sum_for_npress(total):
    ''' Return (a, b) such that a + b == total. '''
    return ['0x' + hex(x)[2:].zfill(4) for x in min(
        ((x, (total - x) % 0x10000) for x in range(0x0101, 0x10000)),
        key=get_npress_adr
    )]

def note(st):
    ''' Print st to stderr. Used for additional information (note, warning) '''
    sys.stderr.write(st)

def to_lowercase(s):
    return s.lower()

def canonicalize(st):
    st = st.strip()
    parts = re.split(r'(".*?")', st)  
    for i in range(len(parts)):
        if i % 2 == 0:
            parts[i] = re.sub(r' *([^a-z0-9]) *', r'\1', parts[i])
    return ''.join(parts)

def del_inline_comment(line):
    return (line + '#')[:line.find('#')].rstrip()

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
        if prev_command == command or prev_adr == address:
            assert False, f'Command appears twice - ' \
                f'first: {prev_command} -> {prev_adr:05X} {prev_tags}, ' \
                f'second: {command} -> {address:05X} {tags} - ' \
                f'{debug_info}'

    command_dict[command] = (address, tuple(tags))

commands = {}
datalabels = {}
disas_filename = None

def get_commands(filename):
    ''' Read a list of gadget names.

    Args:
        A dict
    '''
    global commands
    with open(filename, 'r', encoding='utf-8') as f:
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

        add_command(commands, address, command, tags, f'at {filename}:{line_index0 + 1}')
        
def get_key_map(filename):
    global KEY_MAP
    KEY_MAP = {}
    if not os.path.exists(filename):
        return
    with open(filename, 'r', encoding='utf-8') as f:
        data = f.read().splitlines()
    line_regex = re.compile(r'(?:([0-9A-Fa-f]{4})\s+(\w+)|(\w+)\s+([0-9A-Fa-f]{4}))')
    for line in data:
        line = line.strip()
        if not line or line.startswith('#') or line.startswith('//'):
            continue
        line = del_inline_comment(line)
        if not line:
            continue
        m = line_regex.fullmatch(line)
        if not m:
            continue
        if m[1]:
            hex_raw, key_name = m[1], m[2]
        else:
            key_name, hex_raw = m[3], m[4]
        KEY_MAP[key_name] = f"0x{hex_raw[:2]}, 0x{hex_raw[2:]}"

def get_disassembly(filename):
	'''Try to parse a disasm file with annotated address.

	Each line should look like this:

		mov r2, 1                      ; 0A0A2 | 0201
	'''
	global disasm
	with open(filename, 'r', encoding='u8') as f:
		data = f.read().splitlines()

	line_regex = re.compile(r'\t(.*?)\s*; ([0-9a-fA-F]*) \|')
	disasm = []
	for line in data:
		match = line_regex.match(line)
		if match:
			addr = int(match[2], 16)
			while addr >= len(disasm): disasm.append('')
			disasm[addr] = match[1]

def load_extensions(path):
    if not os.path.exists(path):
        print(f"[WARN] No extension file found: {path}")
        return []

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    pattern = r"---syntax---\s*(.*?)\s*---logic---\s*(.*?)\s*---output---\s*(.*?)\s*(?=---syntax---|$)"
    matches = re.findall(pattern, content, re.DOTALL)

    extensions = []
    for syntax_block, logic_block, output_block in matches:
        extensions.append({
            "syntax": syntax_block.strip(),
            "logic": logic_block.strip(),
            "output": [ln.strip() for ln in output_block.strip().splitlines() if ln.strip()]
        })
    return extensions

def match_extension(line, extensions):
    for ext in extensions:
        syntax = ext["syntax"]
        pattern = re.escape(syntax)
        pattern = re.sub(r'\\\{(\w+)\\\}', r'(?P<\1>.+?)', pattern)
        
        m = re.fullmatch(pattern, line.strip())
        if m:
            return ext, m.groupdict()
    return None, None

def expand_extensions_in_program(program_lines, extensions):
    expanded = []
    for line in program_lines:
        line = line.split('---')[0].strip()
        if not line: continue
        
        current_line = line
        matched_full = False
        
        for ext in sorted(extensions, key=lambda x: len(x["syntax"]), reverse=True):
            pattern_str = re.escape(ext["syntax"]).replace(r"\{", "(?P<").replace(r"\}", ">.+?)")
            
            match = re.fullmatch(pattern_str, current_line)
            is_inline = False
            
            if not match:
                match = re.search(pattern_str, current_line)
                is_inline = True
            
            if match:
                local_env = match.groupdict()
                if ext.get("logic"):
                    try:
                        import random, string, re as re_mod
                        env = vars_dict.copy()
                        env.update(local_env)
                        env.update({"random": random, "string": string, "re": re_mod})
                        exec(ext["logic"], {}, env)
                        local_env.update(env)
                        vars_dict.update(env)
                    except: pass
                
                output_lines = []
                for out in ext["output"]:
                    temp = out
                    for k, v in local_env.items():
                        temp = temp.replace(f"{{{k}}}", str(v))
                    output_lines.append(temp)
                
                if is_inline and len(output_lines) == 1:
                    current_line = current_line[:match.start()] + output_lines[0] + current_line[match.end():]
                else:
                    expanded.extend(output_lines)
                    matched_full = True
                    break
        
        if not matched_full:
            expanded.append(current_line)
    return expanded

def read_rename_list(filename):
    '''Try to parse a rename list.

    If the rename list is ambiguous without disassembly, it raises an error.
    '''
    global commands, datalabels
    with open(filename, 'r', encoding='u8') as f:
        data = f.read().splitlines()

    line_regex   = re.compile(r'^\s*([\w_.]+)\s+([\w_.]+)')
    global_regex = re.compile(r'f_([0-9a-fA-F]+)')
    local_regex  = re.compile(r'.l_([0-9a-fA-F]+)')
    data_regex   = re.compile(r'd_([0-9a-fA-F]+)')
    hexadecimal  = re.compile(r'[0-9a-fA-F]+')

    last_global_label = None
    for line_index0, line in enumerate(data):
        match = line_regex.match(line)
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
                    debug_info=f'at {filename}:{line_index0+1}')
        else:
            raise ValueError('Invalid line: ' + repr(line))

def sizeof_register(reg_name):
    return {'r': 1, 'e': 2, 'x': 4, 'q': 8}[reg_name[0]]

result = []
labels = {}
address_requests = []
relocation_expressions = []
pr_length_cmds = []
deferred_evals = []
home = None
in_comment = False
vars_dict = {}
KEY_MAP = {}

# name of the section currently being processed (from @set.<name>)
current_section_name = None

def handle_label_definition(line):
    """
    Syntax: lbl <label>
    Special: If the label is 'home', it specifies the point to
    start program execution. By default it's at the begin.
    """
    global labels, result
    label = to_lowercase(line.strip()[4:].strip())
    assert label not in labels, f'Duplicate label: {label}'
    labels[label] = len(result)
    
def handle_function_definition(line, program_iter, defined_functions):
    m = re.match(r'func\s+(\w+)\s*\((.*?)\)\s*\{', line.strip())
    if not m: raise ValueError(f"Invalid func definition syntax: {line}")
    func_name, args_str = m.group(1), m.group(2).strip()
    func_args = [arg.strip() for arg in args_str.split(',')] if args_str else []
    
    body = []
    for _, raw_line in program_iter:
        stripped = raw_line.split('---')[0].strip()
        if stripped == '}': break
        if stripped: body.append(stripped)
    defined_functions[func_name] = {"args": func_args, "body": body}

def handle_python_def(line, program_iter, python_functions):
    m = re.match(r'def\s+(\w+)\s*\((.*?)\)\s*\{', line.strip())
    if not m:
        raise ValueError(f"Invalid def syntax: {line}")
    func_name, args_str = m.group(1), m.group(2).strip()
    func_args = [arg.strip() for arg in args_str.split(',')] if args_str else []
    
    raw_body = []
    depth = 1
    for _, raw_line in program_iter:
        content = raw_line.split('---')[0].strip()
        if not content:
            continue
        
        open_count = content.count('{')
        close_count = content.count('}')
        
        if content == '}':
            depth -= 1
            if depth <= 0:
                break
            raw_body.append(content)
            continue
        
        depth += open_count - close_count
        raw_body.append(content)
    
    def convert_block(lines, start_idx):
        """Convert lines with { } blocks into Python indented code.
        Returns (python_lines, next_index)"""
        py_lines = []
        idx = start_idx
        while idx < len(lines):
            line = lines[idx].strip()
            
            if line == '}':
                return py_lines, idx + 1
            
            if line.endswith('{'):
                header = line[:-1].strip()
                inner_lines, idx = convert_block(lines, idx + 1)
                
                if inner_lines:
                    inner_joined = '; '.join(inner_lines)
                    py_lines.append(f"{header}: {inner_joined}")
                else:
                    py_lines.append(f"{header}: pass")
            else:
                py_lines.append(line)
                idx += 1
        
        return py_lines, idx
    
    normalized_body = []
    for line in raw_body:
        s = line.strip()
        while s.startswith('}'):
            normalized_body.append('}')
            s = s[1:].strip()
        
        if not s:
            continue
        
        if s.endswith('}') and not s.startswith('{'):
            if len(s) > 1:
                normalized_body.append(s[:-1].strip())
                normalized_body.append('}')
                continue
        
        normalized_body.append(s)

    converted_lines, _ = convert_block(normalized_body, 0)
    func_src = f"def {func_name}({', '.join(func_args)}):\n"
    if not converted_lines:
        func_src += '    pass\n'
    else:
        for l in converted_lines:
            func_src += '    ' + l + '\n'
    
    try:
        local_ns = {}
        exec(func_src, {"re": re, "os": os, "sys": sys}, local_ns)
        python_functions[func_name] = local_ns[func_name]
    except Exception as e:
        raise ValueError(f"Error compiling Python function {func_name}:\n{e}\nSource:\n{func_src}")

def handle_python_call(line):
    """
    Execute a Python call from assembly.
    If the function returns a string or list of strings, they are processed as assembly lines.
    """
    local_vars = vars_dict.copy()
    local_vars['py'] = PyNamespace(PYTHON_FUNCTIONS)
    try:
        res = eval(line, {"py": local_vars['py']}, local_vars)
        if isinstance(res, str):
            process_line(f'"{res}"')
        elif isinstance(res, int):
            process_line(hex(res))
        elif isinstance(res, list):
            for item in res:
                if isinstance(item, str): process_line(item)
                elif isinstance(item, int): process_line(hex(item))
    except Exception as e:
        raise ValueError(f"Error in Python call {line!r}: {e}")

def handle_repeat_command(line, program_iter):
    """Syntax: repeat <expr> { <lines> }"""
    if line.startswith('repeat '):
        m = re.match(r'repeat\s+(.+?)\s*\{', line.strip())
    elif line.startswith('loop '):
        m = re.match(r'loop\s+(.+?)\s*\{', line.strip())
        
    if not m:
        raise ValueError(f"Invalid repeat syntax: {line}")
    count_expr = m.group(1).strip()
    try:
        eval_scope = vars_dict.copy()
        eval_scope['py'] = PyNamespace(PYTHON_FUNCTIONS)
        count = eval(count_expr, {"py": eval_scope.get('py')}, eval_scope)
        if not isinstance(count, int):
             raise ValueError(f"Repeat count must evaluate to int, got {type(count)}")
    except Exception as e:
        raise ValueError(f"Error evaluating repeat count '{count_expr}': {e}")
    
    body_items = []
    depth = 1
    
    if program_iter is None: 
         raise ValueError("repeat command requires an iterator")

    for item in program_iter:
        if isinstance(item, tuple) and len(item) == 2:
             _, raw_line = item
             content = raw_line
        elif isinstance(item, dict):
             content = item["exec"]
        elif isinstance(item, str):
             content = item
        else:
             content = str(item)

        content_strip = content.split('---')[0].strip()
        if not content_strip:
            continue
        
        open_count = content_strip.count('{')
        close_count = content_strip.count('}')
        
        if content_strip == '}':
            depth -= 1
            if depth <= 0:
                break
            body_items.append(item)
            continue
        
        depth += open_count - close_count
        body_items.append(item)
    
    for i in range(count):
        body_iter = iter(body_items)
        for item in body_iter:
            if isinstance(item, tuple) and len(item) == 2:
                _, raw_line = item
                line_to_proc = raw_line
            elif isinstance(item, dict):
                line_to_proc = item["exec"]
            elif isinstance(item, str):
                line_to_proc = item
            else:
                line_to_proc = str(item)
            
            process_line(line_to_proc, body_iter)

def handle_eval_expression(line):
    expr = line[5:-1].strip()
    expanded_expr = expr
    for var_name, var_value in vars_dict.items():
        pattern = r'\b' + re.escape(var_name) + r'\b'
        expanded_expr = re.sub(pattern, str(var_value), expanded_expr)
    def eval_nested(s, eval_scope):
        pattern = re.compile(r'\beval\(([^()]*(?:\([^()]*\)[^()]*)*)\)')
        while 'eval(' in s:
            matches = list(pattern.finditer(s))
            if not matches:
                break
            for m in reversed(matches):
                inner = m.group(1)
                inner_result = eval_nested(inner.strip(), eval_scope)

                if 'adr(' in inner_result:
                    replacement = f'({inner_result})'
                    s = s[:m.start()] + replacement + s[m.end():]
                    continue
                try:
                    val = eval(inner_result, {"py": eval_scope.get('py')}, eval_scope)
                except Exception as e:
                    raise ValueError(f"Eval error in nested eval('{inner}') (expanded: '{inner_result}'): {e}")
                if isinstance(val, int):
                    val_str = str(val)
                elif isinstance(val, str):
                    val_str = repr(val)
                elif isinstance(val, list) and val:
                    val_str = str(val[0])
                else:
                    raise ValueError(f"Unsupported nested eval result type: {type(val)}")
                s = s[:m.start()] + val_str + s[m.end():]
        return s
    eval_scope = {}
    eval_scope['pr_length'] = len(result)
    eval_scope['py'] = PyNamespace(PYTHON_FUNCTIONS)
    for k, v in vars_dict.items():
        eval_scope[k] = v
    expanded_expr = eval_nested(expanded_expr, eval_scope)
    if 'adr(' in expanded_expr:
        deferred_evals.append((len(result), expanded_expr))
        result.extend((0, 0))
        return
    eval_scope = {}
    eval_scope['pr_length'] = len(result)
    eval_scope['py'] = PyNamespace(PYTHON_FUNCTIONS)
    try:
        val = eval(expanded_expr, {"py": eval_scope.get('py')}, eval_scope)
    except Exception as e:
        raise ValueError(f"Eval error in '{expr}' (expanded: '{expanded_expr}'): {e}")
    if isinstance(val, int):
        process_line(f'0x{val:x}')
    elif isinstance(val, str):
        process_line(f'"{val}"')
    elif isinstance(val, list):
        for item in val:
            if isinstance(item, int):
                process_line(f'0x{item:x}')
            elif isinstance(item, str):
                process_line(f'"{item}"')
    else:
        raise ValueError(f"Unsupported eval result type: {type(val)}")
    
def handle_find_gadgets_command(line, program_iter):
    """
    Syntax:
        find_gadgets {
            gadget1
            gadget2
            ...
        }
    """
    global disas_filename
    gadgets = []
    depth = 1
    current_gadget = []
    
    for item in program_iter:
        if isinstance(item, tuple) and len(item) == 2:
            _, raw_line = item
            content = raw_line
        elif isinstance(item, dict):
            content = item.get("exec", "")
        elif isinstance(item, str):
            content = item
        else:
            content = str(item)
        
        content_strip = content.split('---')[0].strip()
        
        if not content_strip:
            if current_gadget:
                gadgets.append(current_gadget)
                current_gadget = []
            continue
        open_count = content_strip.count('{')
        close_count = content_strip.count('}')
        if content_strip == '}':
            depth -= 1
            if depth <= 0:
                break
            current_gadget.append(content_strip)
            continue
        current_gadget.append(content_strip)
        depth += open_count - close_count
    
    if current_gadget:
        gadgets.append(current_gadget)

    disas_file = disas_filename
    if not disas_file or not os.path.exists(disas_file):
        raise ValueError(f"Disassembly file not found...")
    
    for gadget_lines in gadgets:
        if isinstance(gadget_lines, list):
            instructions = [g for g in gadget_lines if g]
        else:
            instructions = [gadget_lines]
        try:
            adr = find_first_gadget(instructions, disas_file)
            if adr is None:
                raise ValueError("No matching gadget found")
            process_line(f'call {adr}')
            print(f"Gadget found at {adr}: {'; '.join(instructions)}")
        except Exception as e:
            raise ValueError(f"Error finding gadget '{' | '.join(instructions)}': {e}")

def handle_hex_data(line):
    """Syntax: 
        0x<hex_digits>
        hex <hex_digits_reversed>
    """
    global result
    if line.startswith('0x'):
        hex_str = line[2:]
        if len(hex_str) % 2 != 0:
            hex_str = '0' + hex_str
        n_byte = len(hex_str) // 2
        data = int(hex_str, 16)
        for _ in range(n_byte):
            result.append(data & 0xFF)
            data >>= 8
    elif line.startswith('hex'):
        data_str = line[3:].strip()
        assert len(data_str.replace(" ", "")) % 2 == 0, f'Invalid data length'
        data_bytes = bytes.fromhex(data_str)
        result.extend(data_bytes)

def handle_call_command(line):
    """Syntax: `call <address>` or `call <built-in>`."""
    global commands, home
    try:
        adr = int(line[4:], 16)
    except ValueError:
        func_name = line[4:].strip()
        adr, tags = commands[func_name]
        for tag in tags:
            if tag.startswith('warning'):
                note(tag + '\n')

    assert 0 <= adr <= max_call_adr, f'Invalid address: {adr}'
    try:
        if home >= 0xd180 and home < 0xd247:
            process_line(f'0x{adr + 0x30300000:0{8}x}')
        else:
            process_line(f'0x{adr + 0x00000000:0{8}x}')
    except TypeError:
        process_line(f'0x{adr + 0x00000000:0{8}x}')

def handle_goto_command(line):
    """Syntax: `goto <label>`"""
    label = to_lowercase(line[4:])
    process_line(f'er14 = eval(adr({label}) - 0x02);call sp=er14,pop er14')

def handle_address_command(line):
    """
    syntax:
    - adr(label)
    """
    global deferred_evals, result
    
    line_strip = line.strip()
    if line_strip.startswith('adr(') and line_strip.endswith(')'):
        inner_content = line_strip[4:-1].strip()
        
        if ',' in inner_content:
            raise ValueError(f"Invalid adr(...) syntax: {line}")
        
        label_name = inner_content
        expr = f'adr("{label_name}")'
        deferred_evals.append((len(result), expr))
        result.extend((0, 0))
        
    else:
        raise ValueError(f"Unrecognized adr command: {line}")

def handle_data_label(line):
    """`<label>`."""
    global datalabels
    line=datalabels[line.strip()]
    process_line(f'0x{line:x}')

def handle_builtin_command(line):
    """`<built-in>`. Equivalent to `call <built-in>`."""
    line = to_lowercase(line)
    process_line('call ' + line)

def handle_assignment_command(line):
    i = line.index('=')
    left, right = line[:i].strip(), line[i+1:].strip()

    def try_eval(expr):
        try:
            local_vars = vars_dict.copy()
            local_vars['py'] = PyNamespace(PYTHON_FUNCTIONS)
            res = eval(expr, {"py": local_vars['py']}, local_vars)
            return res
        except:
            return expr

    if left.startswith("var "):
        var_name = left[4:].strip()
        val = right
        vars_dict[var_name] = val
    elif left.startswith("reg ") or (left[0] in 'rexq' and any(left.startswith(prefix) for prefix in ['r', 'er', 'xr', 'qr'])):
        register = left[4:].strip() if left.startswith("reg ") else left
        right = right.lower()
        value = right.replace(',', ';')
        process_line(f'call pop {register}')
        l1 = len(result)
        process_line(value)
        assert len(result) - l1 == sizeof_register(register), f'Line {line!r} source/destination target mismatches'
    else:
        val = try_eval(right)
        vars_dict[left] = val

def handle_variable_expansion(line):
    expanded = line

    for var_name, var_value in vars_dict.items():
        pattern = r'\b' + re.escape(var_name) + r'\b'
        expanded = re.sub(pattern, str(var_value), expanded)

    process_line(expanded)

def handle_org_command(line):
    ''' Syntax: `org <expr>`
    Specify the address of this location after mapping.
    Only use this for loader mode.
    '''
    global home, result
    hx = eval(line[3:])
    new_home = hx - len(result)
    assert home is None or home == new_home, 'Inconsistent value of `home`'
    home = new_home

def handle_pr_length_command(line):
    ''' Syntax: `pr_length`
    Defers the calculation of the program length until the end of processing.
    '''
    global pr_length_cmds, result
    pr_length_cmds.append(len(result))
    result.extend((0, 0))

def handle_key_constant(line):
    keyname = line.strip().upper()
    if keyname not in KEY_MAP:
        raise ValueError(f"Unknown key constant: {keyname}. KEY_MAP size: {len(KEY_MAP)}")
    value = KEY_MAP[keyname]
    new_bytes_list = []
    if isinstance(value, str):
        for part in value.split(','):
            part = part.strip()
            new_bytes_list.append(int(part, 0) & 0xFF)
    elif isinstance(value, (list, tuple)):
        new_bytes_list = [int(x) & 0xFF for x in value]
    else:
        raise ValueError(f"Invalid KEY_MAP entry for {keyname}: {value!r}")
    result.extend(new_bytes_list)

def handle_any_string_command(line):
    line_strip = line.strip()
    match = re.search(r'"(.*)"', line_strip)
    if not match:
        return
    content = match.group(1)
    def replace_calc(m):
        return process_line(f"eval({m.group(1)})") or ''
    content = re.sub(r'\{([a-zA-Z_]\w*)\}', replace_calc, content)
    content=content.encode("latin1").decode("utf-8")
    note(f"Processing string: {content.replace('~', ' ')}\n")
    processed_text = re.sub(r"\s", "~", content)
    for c in processed_text:
        try:
            hex_val = char_to_hex[c]
            #print(f"Character '{c}' -> hex value: {hex_val}")  # Debug print
            if len(hex_val) == 2:
                result.append(int(hex_val, 16))
            elif len(hex_val) == 4:
                result.extend([int(hex_val[:2], 16), int(hex_val[2:], 16)])
        except KeyError:
            raise ValueError(f"Character '{c}' not found in conversion table")

def dispatch_command_handler(line, program_iter=None, defined_functions=None):
    line_strip = line.strip()
    if line_strip.lower().startswith('lbl '):
        handle_label_definition(line)
    elif line_strip.startswith("def ") and line_strip.endswith('{'):
        if program_iter is None:
            raise ValueError("Python def handling requires program_iter")
        handle_python_def(line_strip, program_iter, PYTHON_FUNCTIONS)
    elif line_strip.startswith("func "):
        if program_iter is None or defined_functions is None:
            raise ValueError("Function handling requires program_iter and defined_functions")
        handle_function_definition(line, program_iter, defined_functions)
    elif line_strip.startswith("repeat ") or line_strip.startswith("loop "):
        if program_iter is None:
            raise ValueError("Repeat handling requires program_iter")
        handle_repeat_command(line, program_iter)
    elif line_strip.startswith('find_gadgets ') or line_strip.startswith('find_gadgets{'):
        if program_iter is None:
            raise ValueError("find_gadgets handling requires program_iter")
        handle_find_gadgets_command(line, program_iter)
    elif line_strip.startswith('py.'): handle_python_call(line_strip)
    elif line.startswith('0x') or (line.startswith('hex') and 'hex_' not in line): handle_hex_data(line)
    elif (line.startswith('eval(') or line.startswith('calc(')) and line.endswith(')'): handle_eval_expression(line)
    elif line.startswith('call'): handle_call_command(line)
    elif line.startswith('goto'): handle_goto_command(line)
    elif line.startswith('adr'): handle_address_command(line)
    elif line in datalabels: handle_data_label(line)
    elif line in commands: handle_builtin_command(line)
    elif line in vars_dict: handle_variable_expansion(line)
    elif '=' in line: handle_assignment_command(line)
    elif line.startswith('org'): handle_org_command(line)
    elif line.startswith('pr_length'): handle_pr_length_command(line)
    elif line.strip().upper().startswith('KEY_'): handle_key_constant(line)
    elif line_strip.startswith('"'): handle_any_string_command(line_strip)
    else:
        assert False, f'Unrecognized command: {line!r}'

def process_line(line, program_iter=None):
    global result, labels, address_requests, relocation_expressions, pr_length_cmds
    global home, in_comment, vars_dict, deferred_evals
    line = line.split('---')[0].strip()

    if not line or line.isspace():
        return

    if line.startswith('/*'):
        in_comment = True
        return
        
    if '*/' in line:
        in_comment = False
        return
        
    if in_comment:
        return

    elif ';' in line:
        ''' Compound statement. Syntax:
        `<statement1> ; <statement2> ; ...`
        '''
        for command in line.split(';'):
            process_line(to_lowercase(command), program_iter)

    else:
        dispatch_command_handler(line, program_iter)

def finalize_processing():
    global result, labels, address_requests
    global relocation_expressions, pr_length_cmds
    global deferred_evals

    for pos, left_offset, left_label, right_offset, right_label, op in relocation_expressions:
        if left_label not in labels or right_label not in labels:
            raise ValueError(f'Label not found in adr: {left_label}, {right_label}')
        left_addr = labels[left_label] + left_offset
        right_addr = labels[right_label] + right_offset
        
        if op == '+':
            result_addr = (left_addr + right_addr) & 0xFFFF
        else:
            result_addr = (left_addr - right_addr) & 0xFFFF
        
        if result[pos] != 0 or result[pos+1] != 0:
            print(f"[WARN] adr overwrite at {pos:04X}")
        result[pos] = result_addr & 0xFF
        result[pos + 1] = (result_addr >> 8) & 0xFF

    for pos in pr_length_cmds:
        pr_length = len(result)
        if result[pos] != 0 or result[pos+1] != 0:
            print(f"[WARN] pr_length overwrite at {pos:04X}")
        result[pos] = pr_length & 0xFF
        result[pos + 1] = (pr_length >> 8) & 0xFF

    relocation_expressions.clear()
    pr_length_cmds.clear()



def _split_into_sections(program_lines):
    """Return list of (name, lines) tuples by splitting on @set.<name> directives.
    Lines before the first @set are grouped under name None.  The directive
    itself is not included in the section contents.
    """
    sections = []
    current_name = None
    current_lines = []
    for raw_line in program_lines:
        stripped = raw_line.strip()
        if stripped.startswith('@set.'):
            # begin a new section
            if current_name is not None or current_lines:
                sections.append((current_name, current_lines))
            current_name = stripped[5:]
            current_lines = []
        else:
            current_lines.append(raw_line)
    # append last
    if current_name is not None or current_lines:
        sections.append((current_name, current_lines))
    return sections


def process_program(args, program_lines, overflow_initial_sp):
    # split into sections and dispatch to helper for each
    sections = _split_into_sections(program_lines)
    # reorder so named sections come before unnamed to avoid warning prints
    named = [(n, l) for n, l in sections if n is not None]
    unnamed = [(n, l) for n, l in sections if n is None]
    sections = named + unnamed

    if len(sections) == 1:
        # simple case, just process the single list of lines
        return _process_program_core(args, sections[0][1], overflow_initial_sp)

    # multiple sections: process each independently
    global current_section_name
    for name, lines in sections:
        current_section_name = name
        if name is not None:
            print(f"\n=== section @{name} ===")
        _process_program_core(args, lines, overflow_initial_sp)
    current_section_name = None


def _process_program_core(args, program_lines, overflow_initial_sp):
    # original body moved here unchanged
    global result, labels, address_requests
    global relocation_expressions, pr_length_cmds, home
    global in_comment, note
    global deferred_evals, vars_dict

    result = []
    labels = {}
    address_requests = []
    relocation_expressions = []
    pr_length_cmds = []
    deferred_evals = []
    home = None
    in_comment = False
    # vars_dict = {}
    final_lines_to_process = []
    defined_functions = {}
    
    orig_line_map = []
    for idx, raw_line in enumerate(program_lines):
        orig_line_map.append(idx + 1)

    program_iter = iter(enumerate(program_lines))
    for line_index, raw_line in program_iter:
        line = canonicalize(del_inline_comment(raw_line))

        line_strip = line.strip()
        if line_strip.startswith("func "):
            handle_function_definition(line, program_iter, defined_functions)
            continue

        if line_strip.startswith("def ") and line_strip.endswith('{'):
            handle_python_def(line_strip, program_iter, PYTHON_FUNCTIONS)
            continue

        m = re.match(r'(\w+)\s*\((.*?)\)', line.strip())
        if m and m.group(1) in defined_functions:
            called_func_name = m.group(1)
            func = defined_functions[called_func_name]
            call_args_str = m.group(2)
            call_args = re.findall(r'("(?:[^"\\]|\\.)*"|[^,]+)', call_args_str)
            call_args = [arg.strip() for arg in call_args]
            if call_args == [''] and not call_args_str: call_args = []

            if len(call_args) != len(func["args"]):
                raise ValueError(f"Error calling function {line}: args mismatch")

            for param_def, arg_val in zip(func["args"], call_args):
                if param_def.strip():
                    final_lines_to_process.append({
                        "exec": f"{param_def.strip()} = {arg_val}",
                        "raw": raw_line, "num": orig_line_map[line_index], "ctx": f"passing args to '{called_func_name}'"
                    })
            for line_in_func in func["body"]:
                final_lines_to_process.append({"exec": line_in_func, "raw": line_in_func, "num": orig_line_map[line_index], "ctx": f"inside '{called_func_name}'"})
            continue

        final_lines_to_process.append({"exec": line, "raw": raw_line, "num": orig_line_map[line_index], "ctx": ""})

    lines_iter = iter(final_lines_to_process)
    for item in lines_iter:
            if isinstance(item, dict):
                line = item["exec"]
                raw_origin = item["raw"]
                line_num = item["num"]
                context = item.get("ctx", "")
            else:
                line = item
                raw_origin = item
                line_num = "?"
                context = ""
            
            line_strip = canonicalize(del_inline_comment(line))

            if not line_strip.startswith('"'):
                line_to_process = to_lowercase(line_strip)
            else:
                line_to_process = line_strip

            if not line_to_process:
                continue

            note_log = ''
            original_note_func = note

            def local_note_func(st):
                nonlocal note_log
                note_log += st
            
            note = local_note_func
            old_len_result = len(result)
            
            try:
                process_line(line_to_process, lines_iter)
            except Exception as e:
                print(f"\nTraceback (most recent call last):")
                ctx_info = f", {context}" if context else ""
                fname = os.path.basename(args.input_file) if hasattr(args, 'input_file') else "?"
                if fname != "?":
                    print(f"  File \"{fname}\", line {line_num}{ctx_info}")
                else:
                    print(f"  In line {line_num}{ctx_info}")
                print(f"    {raw_origin.strip()}")
                print(f"    {"^" * len(raw_origin.strip())}")
                print(f"CompilerError: {str(e)}")
                sys.exit()

            if args.format == 'key' and \
                    any(x != 0 and get_npress(x) > 100 for x in result[old_len_result:]):
                local_note_func('Line generates many keypresses\n')

            note = original_note_func
            if note_log:
                note(f'While processing line\n{line}\n')
                note(note_log)

    eval_scope = {}
    for k, v in vars_dict.items():
        if isinstance(v, list):
             eval_scope[k] = int.from_bytes(bytes(v), 'little')
        else:
             eval_scope[k] = v

    for label_name in labels.keys():
         if label_name not in eval_scope:
            eval_scope[label_name] = label_name

    def adr_eval(label, offset=0):
        if not isinstance(label, str):
             raise ValueError(f"Label in adr() must be a string, but got {label} (type {type(label)})")
        if label not in labels:
            raise ValueError(f'Label not found during deferred eval: {label}')
        return (labels[label] + offset)

    eval_scope['adr'] = adr_eval
    home_dependent_evals = [] 
    temp_deferred_evals = list(deferred_evals)
    deferred_evals.clear() 
    
    for pos, expr in temp_deferred_evals:
        try:
            val = eval(expr, {}, eval_scope)
        except Exception as e:
            try:
                temp_scope = eval_scope.copy()
                for k, v in temp_scope.items():
                    if isinstance(v, str) and v.startswith("eval("):
                         temp_scope[k] = eval(v[5:-1], {}, temp_scope)
                val = eval(expr, {}, temp_scope)
            except Exception as e2:
                 raise ValueError(f"Deferred eval error in expression {expr!r}: {e2}")
        
        if not isinstance(val, int):
            raise ValueError(f"Deferred eval {expr!r} did not return an integer")
        
        is_absolute_address = expr.count('adr(') > 1
        
        if is_absolute_address:
            val = val & 0xFFFF
            if result[pos] != 0 or result[pos+1] != 0:
                print(f"[WARN] eval_abs overwrite at {pos:04X}")
            result[pos] = val & 0xFF
            result[pos + 1] = (val >> 8) & 0xFF
        else:
            home_dependent_evals.append((pos, val))
            
    finalize_processing()
    
    resolved_adr_cmds = []
    for source_adr, offset, target_label in address_requests:
        if target_label not in labels:
             raise ValueError(f'Label not found: {target_label} (for adr() at pos {source_adr})')
        resolved_adr_cmds.append((source_adr, labels[target_label] + offset))
    
    address_requests.clear()
    if args.target in ('none', 'overflow'):
        if args.target == 'overflow':
            assert len(result) <= 100, 'Program too long'

        if home is None:
            home = overflow_initial_sp
            if 'home' in labels:
                home -= labels['home']
                if home + len(result) > 0x8E00:
                    # suppress warning if section has a name (assuming named sections are handled first)
                    if current_section_name is None:
                        note(f'Warning: Program length after home = {len(result)} bytes'
                            f' > {0x8E00 - home} bytes\n')

            min_home = home
            while min_home >= 0x8154 + 200:
                min_home -= 100
            while home + len(result) <= 0x8E00:
                home += 100
            
            all_home_dependencies = resolved_adr_cmds + home_dependent_evals
            
            home = min(range(min_home, home, 100), key=lambda home_val:
                        (
                            sum(
                                get_npress_adr(home_val + home_offset) >= 100
                                for source_adr, home_offset in all_home_dependencies
                            ),
                            -home_val
                        )
                        )

    elif args.target == 'loader':
        if home is None:
            home = 0x85b0 - len(result)
            entry = home + labels.get('home', 0) - 2
            result.extend((0x6a, 0x4f, 0, 0, entry & 255, entry >> 8, 0x68, 0x4f, 0, 0))
            while home + len(result) < 0x85d7:
                result.append(0)
            result.extend((0xff, 0xae, 0x85))
            home2 = 0
            assert (home - home2) >= 0x8501, 'Program too long'
            while get_npress_adr(home - home2) >= 100:
                home2 += 1

    else:
        assert False, 'Internal error'

    assert home is not None

    for source_adr, home_offset in resolved_adr_cmds:
        target_adr = home + home_offset
        if result[source_adr] != 0 or result[source_adr + 1] != 0:
            print(f"[WARN] adr overwrite at {source_adr:04X}, old={result[source_adr]:02X}{result[source_adr+1]:02X}")
        result[source_adr] = target_adr & 0xFF
        result[source_adr + 1] = target_adr >> 8

    for source_adr, home_offset in home_dependent_evals:
        target_adr = home + home_offset
        if result[source_adr] != 0 or result[source_adr + 1] != 0:
            print(f"[WARN] eval_adr overwrite at {source_adr:04X}, old={result[source_adr]:02X}{result[source_adr+1]:02X}")
        result[source_adr] = target_adr & 0xFF
        result[source_adr + 1] = target_adr >> 8

    for label, home_offset in labels.items():
        note(f'Label {label} is at address {home + home_offset:04X}\n')
            
    if args.target == 'overflow':
        hackstring = list(map(ord, '1234567890' * 10))
        for home_offset, byte in enumerate(result):
            assert isinstance(byte, int), (home_offset, byte)
            hackstring_pos = (home + home_offset - 0x8154) % 100
            hackstring[hackstring_pos] = byte

    # wrap output with section header/footer if needed
    header_printed = False
    def _print_header():
        nonlocal header_printed
        if header_printed:
            return
        header_printed = True
        print(f"=== {home:#06x} -> {home + len(result):#06x} ===")
    def _print_footer():
        print('=====')
        
    if home == home+len(result) and current_section_name is None:
        return

    _print_header()

    if args.target == 'overflow' and args.format == 'hex':
        print(''.join(f'{byte:02x}' for byte in hackstring))

    elif args.target == 'none' and args.format == 'hex':
        print(f'{home:#06x}:', ' '.join(f'{b:02x}' for b in result))

    elif args.target == 'none' and args.format == 'key':
        print(f'{home:#06x}:', ' '.join(byte_to_key(b) for b in result))

    elif args.target == 'loader' and args.format == 'key':
        addr = home - home2
        print('Address to load:',
            byte_to_key(addr & 0xff),
            byte_to_key((addr >> 8) & 0xff))

        result = [0] * home2 + result

        import keypairs
        print(keypairs.format(result))

    elif args.target == 'overflow' and args.format == 'key':
        print(' '.join(byte_to_key(x) for x in hackstring))

    else:
        raise ValueError('Unsupported target/format combination')

    _print_footer()

rom = None

def get_rom(x):
    global rom

    if isinstance(x, str):
        with open(x, 'rb') as f:
            rom = f.read()
    elif isinstance(x, bytes):
        rom = x
    else:
        raise TypeError

def find_equivalent_addresses(rom_data: bytes, address_queue: set):
    from collections import defaultdict
    comefrom = defaultdict(list)

    for i in range(0, len(rom_data), 2):  # BC AL
        if rom_data[i + 1] == 0xce:
            offset = rom_data[i]
            if offset >= 128:
                offset -= 256
            target_addr = i >> 16 | ((i + (offset + 1) * 2) & 0xffff)
            comefrom[target_addr].append(i)

    for i in range(0, len(rom_data) - 2, 2):  # B
        if (
                rom_data[i] == 0x00 and
                (rom_data[i + 1] & 0xf0) == 0xf0):
            target_addr = (rom_data[i + 1] & 0x0f) << 16 | rom_data[i + 3] << 8 | rom_data[i + 2]
            comefrom[target_addr].append(i)

    for i in range(0, len(rom_data) - 4, 2):  # BL / POP PC
        if (
                rom_data[i] == 0x01 and
                (rom_data[i + 1] & 0xf0) == 0xf0 and
                (rom_data[i + 4] & 0xf0) == 0x8e and
                (rom_data[i + 5] & 0xf0) == 0xf2):
            target_addr = (rom_data[i + 1] & 0x0f) << 16 | rom_data[i + 3] << 8 | rom_data[i + 2]
            comefrom[target_addr].append(i)

    ans = set()
    while address_queue:
        adr = address_queue.pop()
        if adr in ans:
            continue
        ans.add(adr)

        if adr in comefrom:
            address_queue.update(comefrom[adr])

    return ans

def optimize_gadget_from_rom(rom_data: bytes, gadget_bytes: bytes) -> set:
    assert len(gadget_bytes) % 2 == 0
    pending_addresses = set()
    
    for i in range(0, len(rom_data) - len(gadget_bytes) + 1, 2):
        if rom_data[i:i + len(gadget_bytes)] == gadget_bytes:
            pending_addresses.add(i)

    return find_equivalent_addresses(rom_data, pending_addresses)

def optimize_gadget(gadget_bytes: bytes) -> set:
    global rom
    return optimize_gadget_from_rom(rom, gadget_bytes)

def print_addresses(adrs, n_preview: int):
    global disasm 
    
    adrs = list(map(optimize_adr_for_npress, adrs))
    for adr in sorted(adrs, key=get_npress_adr):
        keys = ' '.join(map(byte_to_key,
                            (adr & 0xff, (adr >> 8) & 0xff, 0x30 | adr >> 16)
                            ))
        print(f'{adr:05x}  {get_npress_adr(adr):3}    {keys:20}')

        i = adr & 0x3FFFE
        count = 0
        while count < n_preview and i < len(disasm):
            opcode = disasm[i]
            if opcode != 0:
                label_name = globals().get('labels', {}).get(i, "")
                label_str = f" <{label_name}>" if label_name else ""
                
                print(f'    {i:05x}: {opcode:04x}{label_str}')
                count += 1
            i += 2