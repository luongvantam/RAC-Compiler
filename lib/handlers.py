import re
import utils
import loader
import difflib
from loader import sizeof_register, char_to_hex, token_to_hex

sorted_tokens = sorted(token_to_hex.keys(), key=len, reverse=True)

def process_line(line, program_iter=None):
    from engine import process_line as _process_line
    return _process_line(line, program_iter)

def handle_label_definition(line):
    line_str = line.strip()
    label = line_str[4:].strip().lower() if line_str.lower().startswith('lbl ') else line_str[:-1].strip().lower()
    
    at_match = re.search(r'\s+at\s+(.+)$', label)
    if at_match:
        address_expr = at_match.group(1)
        label_name = label[:at_match.start()].strip()
        address = int(utils.safe_eval(address_expr))
        
        if label_name in loader.labels: raise ValueError(f'Duplicate label: {label_name}')
        if hasattr(loader, 'global_labels'):
            if label_name in loader.global_labels and loader.global_labels[label_name] != address:
                pass # allow across passes if address matches? Actually just overwrite or keep. Overwrite is safe.
            loader.global_labels[label_name] = address
            if getattr(loader, 'current_section_name', None) is not None or not getattr(loader, 'is_pass1', False):
                # We need to make sure we don't print twice, but just printing is fine.
                pass
            if not getattr(loader, 'is_pass1', False):
                utils.note(f'Label {label_name} is at address {address:04X} (absolute)\n')
        return

    if label in loader.labels: raise ValueError(f'Duplicate label: {label}')
    loader.labels[label] = len(loader.result)

def collect_block_body(first_line_rest, program_iter, line_num=None):
    if '}' in first_line_rest:
        content = first_line_rest[:first_line_rest.rfind('}')].strip()
        return ([(line_num, content)] if content and line_num is not None else [content] if content else []), True

    body_items, depth = [], 1
    if program_iter is None: raise ValueError("Block requires an iterator")
        
    for item in program_iter:
        ln, content = item if isinstance(item, tuple) and len(item) == 2 else (None, item.get("exec") if isinstance(item, dict) else str(item))
        content_strip = content.strip()
        if not content_strip: continue
            
        depth += content_strip.count('{') - content_strip.count('}')
        if depth <= 0:
            if '}' in content_strip:
                before_close = content_strip[:content_strip.find('}')].strip()
                if before_close:
                    if isinstance(item, dict):
                        d = item.copy()
                        d["exec"] = before_close
                        body_items.append(d)
                    else: body_items.append((ln, before_close) if ln is not None else before_close)
            break
        body_items.append(item)
    return body_items, False

def handle_function_definition(line, program_iter):
    m = re.match(r'func\s+(\w+)\s*\((.*?)\)\s*\{', line.strip())
    if not m: raise ValueError(f"Invalid func syntax: {line}. Expected 'func name(args) {{'")
    func_name, args_str = m.group(1), m.group(2).strip()
    
    line_num = getattr(loader, 'current_line_num', None)
    body_items, _ = collect_block_body(line[m.end():].strip(), program_iter, line_num)
    
    body, return_expr = [], None
    for item in body_items:
        b_ln, content = item if isinstance(item, tuple) and len(item) == 2 else (item.get("num"), item.get("exec")) if isinstance(item, dict) else (line_num, str(item))
        stripped = content.strip()
        if not stripped: continue
        if stripped.startswith('return '):
            if return_expr is not None: raise ValueError(f"Multiple returns in {func_name}")
            return_expr = stripped[7:].strip()
        else:
            body.append((b_ln, stripped))
            
    if return_expr is not None and body: raise ValueError(f"Function {func_name} with return must ONLY contain return")
    loader.defined_functions[func_name] = {"args": [a.strip() for a in args_str.split(',')] if args_str else [], **({"return_expr": return_expr} if return_expr is not None else {"body": body})}

def handle_repeat_command(line, program_iter):
    m = re.match(r'(?:repeat|loop)\s+(.+?)\s*\{', line.strip())
    if not m: raise ValueError(f"Invalid repeat syntax: {line}. Expected 'repeat count {{'")
    try: count = int(utils.safe_eval(m.group(1).strip(), loader.vars_dict.copy()))
    except Exception as e: raise ValueError(f"Error eval repeat count '{m.group(1)}': {e}")
        
    line_num = getattr(loader, 'current_exec_info', {}).get('num')
    body_items, _ = collect_block_body(line[m.end():].strip(), program_iter, line_num)
    
    for _ in range(count):
        b_iter = iter(body_items)
        for item in b_iter:
            if isinstance(item, dict):
                loader.current_exec_info = {"line": item["exec"], "raw": item.get("raw", ""), "num": item.get("num"), "ctx": item.get("ctx", "")}
                process_line(item["exec"], b_iter)
            elif isinstance(item, tuple) and len(item) == 2:
                loader.current_exec_info = {"line": item[1], "raw": item[1], "num": item[0], "ctx": ""}
                process_line(item[1], b_iter)
            else:
                process_line(str(item), b_iter)

def handle_eval_expression(line):
    expr = line[5:-1].strip()
    expr = re.sub(r'adr\(\s*\$\s*\)', 'adr("$")', expr)
    expanded_expr = re.sub(r'\bpr_length\b', 'sizeof()', expr)
    
    if loader.vars_dict:
        pat = re.compile(r'\b(' + '|'.join(re.escape(k) for k in loader.vars_dict) + r')\b')
        expanded_expr = pat.sub(lambda m: str(loader.vars_dict[m.group(1)]), expanded_expr)

    expanded_expr = re.sub(r'\bdist\.(\w+)\b', r'dist("\1")', expanded_expr)
    expanded_expr = re.sub(r'\bsizeof\((.*?)\)', lambda m: f'sizeof("{m.group(1).strip()}")', expanded_expr)

    eval_scope = {'pr_length': len(loader.result), **loader.vars_dict}

    def eval_nested(s):
        while 'eval(' in s:
            s_old = s
            for m in reversed(list(re.finditer(r'\beval\(([^()]*(?:\([^()]*\)[^()]*)*)\)', s))):
                inner = m.group(1).strip()
                inner_res = eval_nested(inner)
                if 'adr(' in inner_res: s = s[:m.start()] + f"({inner_res})" + s[m.end():]
                else: s = s[:m.start()] + str(utils.safe_eval(inner_res, eval_scope) if type(utils.safe_eval(inner_res, eval_scope)) is not list else utils.safe_eval(inner_res, eval_scope)[0]) + s[m.end():]
            if s == s_old: break
        return s
        
    expanded_expr = eval_nested(expanded_expr)
    
    if 'adr(' in expanded_expr or 'sizeof(' in expr or 'dist.' in expr:
        loader.deferred_evals.append((len(loader.result), expanded_expr, getattr(loader, 'current_exec_info', {})))
        loader.result.extend((0, 0))
        return
        
    val = utils.safe_eval(expanded_expr, eval_scope)
    
    if isinstance(val, (int, list)):
        max_len = max([2] + [(len(m) + len(m)%2) for m in re.findall(r'\b0x([0-9a-fA-F]+)\b', expanded_expr)])
        for item in (val if isinstance(val, list) else [val]):
            process_line(f'0x{item:0{max_len}x}' if isinstance(item, int) else f'"{item}"')
    elif isinstance(val, str):
        process_line(f'"{val}"')
    else: raise ValueError(f"Unsupported eval type: {type(val)}")

def handle_list_command(line, program_iter):
    content = line[1:]
    parts = [content.split(']')[0]] if ']' in content else [content] + [s.split(']')[0] if ']' in s else s for s in (item[1].strip() if isinstance(item, tuple) else item.get("exec", "").strip() if isinstance(item, dict) else str(item).strip() for item in program_iter) if s]
    process_line("\n".join(parts).replace('\n', ';'))

def handle_hex_data(line):
    if line.startswith('0x'):
        h = line[2:]
        if len(h) % 2: h = '0' + h
        val = int(h, 16)
        for _ in range(len(h) // 2):
            loader.result.append(val & 0xFF)
            val >>= 8
    else:
        loader.result.extend(bytes.fromhex(line[3:].strip()))

def handle_call_command(line):
    cmd = line[4:].strip()
    try: adr = int(cmd, 16)
    except ValueError:
        if cmd not in loader.commands:
            matches = difflib.get_close_matches(cmd, loader.commands.keys(), n=1, cutoff=0.6)
            if matches: raise ValueError(f"Call target not found: {cmd!r}. Did you mean {matches[0]!r}?")
            raise ValueError(f"Call target not found: {cmd!r}")
        adr, tags = loader.commands[cmd]
        for t in tags: 
            if t.startswith('warning'): utils.note(t + '\n')
            
    build_config = getattr(loader, 'build_config', {})
    if 'line.gadgets' in build_config:
        offset = build_config['line.gadgets']
    else:
        try: irange = loader.datalabels['input_range'] if 'input_range' in loader.datalabels else loader.datalabels['input_area']
        except Exception: irange = -1
        offset = 0x30300000 if loader.home and irange <= loader.home < irange + 0xc8 else 0
    
    process_line(f'0x{adr + offset:08x}')

def handle_goto_command(line):
    parts = line.split(maxsplit=1)
    if len(parts) < 2: raise ValueError(f"Invalid goto syntax: {line}. Expected 'goto <label>'")
    lbl = parts[1].lower()
    reg = 'er6' if line.startswith('goto_er6') else 'er14'
    process_line(f'{reg} = eval(adr("{lbl}") - 0x02);call sp={reg},pop {"er8" if reg=="er6" else reg}')

def handle_address_command(line):
    inner = line.strip()[4:-1].strip()
    parts = [p.strip() for p in inner.split(',')]
    if not parts or not parts[0] or len(parts) > 3: raise ValueError(f"Invalid adr syntax: {line}. Expected 'adr(label, offset, base)'")
    
    expr = [f'adr("{parts[0]}")']
    if len(parts) > 1 and parts[1]: expr.append(parts[1] if parts[1].startswith(('+','-')) else '+' + parts[1].replace(" ",""))
    if len(parts) > 2 and parts[2]:
        diff = int(parts[2].replace(" ",""), 0) - (loader.home or 0)
        expr.append(f'+{diff}' if diff >= 0 else str(diff))
        
    if len(expr) == 1:
        loader.deferred_evals.append((len(loader.result), expr[0], getattr(loader, 'current_exec_info', {})))
        loader.result.extend((0, 0))
    else: process_line(f'eval({" ".join(expr)})')

def handle_define_gadget_command(line):
    if ':' not in line: raise ValueError(f"Invalid def syntax: {line}. Expected 'def name: address'")
    cmd, addr_str = [x.strip() for x in line[3:].strip().split(':', 1)]
    cmd = utils.canonicalize(cmd).lower()
    tags = []
    while cmd.startswith('{'):
        end = cmd.find('}')
        if end < 0: raise Exception(f'Unmatched "{{" in inline def command: {line}')
        tags.append(cmd[1:end])
        cmd = cmd[end+1:].strip()
    
    try:
        addr = int(addr_str, 16)
    except ValueError:
        raise ValueError(f"Invalid address in def: {addr_str}")
    loader.add_command(loader.commands, addr, cmd, tags, 'inline def')
    utils.note(f"Gadget {cmd} is {addr_str}\n")

def handle_assignment_command(line, program_iter):
    l, r = [x.strip() for x in line.split('=', 1)]
    
    m_func = re.match(r'^(\w+)\s*\(((?:[^()]+|\([^()]*\))*)\)$', r)
    if m_func and m_func.group(1) in getattr(loader, 'defined_functions', {}):
        f = loader.defined_functions[m_func.group(1)]
        if "return_expr" not in f: raise ValueError(f"Func {m_func.group(1)} cannot be assigned (no return)")
        args = [a.strip() for a in re.findall(r'("(?:[^"\\]|\\.)*"|[^,]+)', m_func.group(2))]
        if args == [''] and not m_func.group(2): args = []
        if len(args) != len(f["args"]): raise ValueError(f"Args mismatch in {r}")
        r = f["return_expr"]
        for p, a in zip(f["args"], args): r = re.sub(r'\b' + re.escape(p) + r'\b', a, r)

    if r.startswith('['):
        if ']' in r[1:]:
            parts = [r[1:].split(']')[0]]
        else:
            parts = [r[1:]]
            if program_iter:
                for i in program_iter:
                    s = i[1] if isinstance(i, tuple) else i.get("exec", "") if isinstance(i, dict) else str(i)
                    if not s: continue
                    if ']' in s:
                        parts.append(s.split(']')[0])
                        break
                    parts.append(s)
        r = ";".join(parts)

    if l.startswith("var "):
        loader.vars_dict[l[4:].strip()] = r
        utils.note(f"Variable '{l[4:].strip()}' set to {r}\n")
    elif l.startswith("reg ") or re.match(r'^(?:ea|lr|(?:r|er|xr|qr)\d+)\b', l):
        reg = l[4:].strip() if l.startswith("reg ") else l
        paren_balance, new_right = 0, []
        for char in r.lower():
            if char == '(': paren_balance += 1
            elif char == ')': paren_balance -= 1
            new_right.append(';' if char == ',' and paren_balance == 0 else char)
        process_line(f'call pop {reg}')
        l1 = len(loader.result)
        process_line("".join(new_right))
        if len(loader.result) - l1 != sizeof_register(reg): raise ValueError(f"Line {line!r} source/dest target mismatches")
    elif l.startswith("lbl "):
        process_line(l)
        process_line(r)
    else:
        loader.vars_dict[l] = r
        utils.note(f"Variable '{l}' set to {r}\n")

def handle_variable_expansion(line):
    if not loader.vars_dict: return process_line(line)
    def repl(m):
        v, idx = m.group(1), m.group(2) if len(m.groups()) > 1 else None
        val = str(loader.vars_dict[v])
        if idx is not None:
            i = int(idx)
            if val.startswith('"') and val.endswith('"'): return f'"{val[1:-1][i]}"' if 0 <= i < len(val)-2 else ''
            if ';' in val: items = [x.strip() for x in val.split(';') if x.strip()]; return items[i] if 0 <= i < len(items) else ''
        return val
    pat = r'\b(' + '|'.join(re.escape(k) for k in loader.vars_dict) + r')(?:\s*\[(\d+)\])?\b'
    process_line(re.sub(pat, repl, line))

def handle_string_command(line):
    m = re.search(r'"(.*)"', line.strip())
    if not m: return
    content = re.sub(r'\{([a-zA-Z_]\w*(?:\[\d+\])?)\}', lambda x: process_line(f"eval({x.group(1)})") or '', m.group(1))
    for c in re.sub(r"\s", "~", content.encode("latin1").decode("utf-8")):
        try:
            hx = char_to_hex[c]
            if len(hx) == 2: loader.result.append(int(hx, 16))
            else: loader.result.extend([int(hx[:2], 16), int(hx[2:], 16)])
        except KeyError: raise ValueError(f"Char '{c}' not found")

def handle_token_literal(line):
    content = line.strip()[1:-1].replace(" ", "")
    i = 0
    while i < len(content):
        for t in sorted_tokens:
            if content.startswith(t, i):
                hx = token_to_hex[t]
                if len(hx) == 2: loader.result.append(int(hx, 16))
                else: loader.result.extend([int(hx[:2], 16), int(hx[2:], 16)])
                i += len(t)
                break
        else:
            hx = token_to_hex.get(content[i])
            if not hx: raise ValueError(f"Unknown token: {content[i]}")
            if len(hx) == 2: loader.result.append(int(hx, 16))
            else: loader.result.extend([int(hx[:2], 16), int(hx[2:], 16)])
            i += 1

def handle_adr_of_hd_command(line):
    m = re.match(r'^adr_of\s*(?:\[(.*?)\]\s*)?(?:\[(.*?)\]\s*)?(\S+)$', line.strip())
    if not m: raise ValueError(f"Invalid adr_of syntax: {line}. Expected 'adr_of [offset] [base] label'")
    offset, base, lbl = m.group(1) or "+ 0", m.group(2), m.group(3)
    process_line(f'adr({lbl}, {offset.strip()}{f", {base}" if base else ""})')

def handle_adr_arith_hd_command(line):
    content = line.strip()[9:].strip()
    pairs = re.findall(r'(?:\[([^\]]+)\])?\s*([a-zA-Z_]\w*)', content)
    ops = [o[0] or o[1] for o in re.findall(r'\]\s*([+-])\s*(?:\[|\w)|(?:\s|[a-zA-Z_]\w*)\s*([+-])\s*(?:\[|[a-zA-Z_]\w*)', content)]
    if not pairs or len(pairs)-1 != len(ops): raise ValueError(f"Invalid adr_arith syntax: {line}. Expected 'adr_arith [offset1] label1 + [offset2] label2'")
    expr_parts = []
    for (off, lbl), op in zip(pairs, ops + ['']):
        off = off.strip() if off else None
        sub = f'adr("{lbl}")' if not off else f'adr("{lbl}") {off[0]} {off[1:].strip()}' if off.startswith(('+','-')) else f'adr("{lbl}") + {off}'
        expr_parts.append(f'({sub}) {op}'.strip())
    process_line(f"eval({' '.join(expr_parts)[:-2].strip() if not expr_parts[-1][-1].isalnum() else ' '.join(expr_parts)})")

def handle_str_hd_command(line):
    content = line.strip()[3:].strip()
    m_var_str = re.match(r'^([a-zA-Z_]\w*)\s+"([^"]*)"$', content)
    if m_var_str: loader.vars_dict[m_var_str.group(1)] = m_var_str.group(2); return
    val = content[1:-1] if re.match(r'^"([^"]*)"$', content) else str(loader.vars_dict.get(content, "")) if re.match(r'^([a-zA-Z_]\w*)$', content) else None
    if val is None: raise ValueError(f"Invalid str syntax: {line}. Expected 'str \"string\"' or 'str var'")
    for c in re.sub(r"\s", "~", val.encode("latin1").decode("utf-8")):
        hx = char_to_hex[c]
        if len(hx) == 2: loader.result.append(int(hx, 16))
        else: loader.result.extend([int(hx[:2], 16), int(hx[2:], 16)])

def dispatch_command_handler(line, program_iter=None, defined_functions=None):
    ls = line.strip()
    if ls.startswith('org'):
        new_home = utils.safe_eval(ls[3:]) - len(loader.result)
        if loader.home is not None and loader.home != new_home: raise ValueError('Inconsistent value of `home`')
        loader.home = new_home
    elif ls.startswith('backup '): loader.backup_address = int(utils.safe_eval(ls[6:]))
    elif ls.startswith('"'): handle_string_command(ls)
    elif ls.startswith("'"): handle_token_literal(ls)
    elif ls.startswith('0x') or (ls.startswith('hex') and 'hex_' not in ls):
        if ls.startswith('0x') and not re.match(r'^0x[0-9a-fA-F]+$', ls): handle_eval_expression(f"eval({ls})")
        else: handle_hex_data(ls)
    elif ls in loader.datalabels: process_line(f'0x{loader.datalabels[ls]:x}')
    elif ls in loader.commands: process_line('call ' + ls)
    elif ls.startswith('call'): handle_call_command(ls)
    elif ls.startswith(('def ', '@def ')): handle_define_gadget_command(ls)
    elif '=' in ls: handle_assignment_command(ls, program_iter)
    elif (ls.lower().startswith('lbl ') or ":" in ls) and 'def' not in ls: handle_label_definition(ls)
    elif ls.startswith("func"): handle_function_definition(ls, program_iter)
    elif ls.startswith(("repeat", "loop")) and not ls.startswith('loop_'): handle_repeat_command(ls, program_iter)
    elif (ls.startswith('eval(') or ls.startswith('calc(')) and ls.endswith(')'): handle_eval_expression(ls)
    elif ls.startswith(('goto', 'goto_er14', 'goto_er6')): handle_goto_command(ls)
    elif ls.startswith('adr('): handle_address_command(ls)
    elif re.match(r'^\w+(\[\d+\])?$', ls) and re.match(r'^\w+', ls).group(0) in loader.vars_dict: handle_variable_expansion(ls)
    elif ls.startswith('pr_length'): loader.sizeof_cmds.append((len(loader.result), getattr(loader, 'current_section_name', None), getattr(loader, 'current_exec_info', {}))); loader.result.extend((0, 0))
    elif ls.startswith('sizeof(') or ls == 'sizeof()':
        m = re.match(r'^sizeof\((.*?)\)$', ls)
        loader.sizeof_cmds.append((len(loader.result), m.group(1).strip() if m and m.group(1).strip() else getattr(loader, 'current_section_name', None), getattr(loader, 'current_exec_info', {})))
        loader.result.extend((0, 0))
    elif ls.startswith('['): handle_list_command(ls, program_iter)
    elif ls.startswith('adr_of'): handle_adr_of_hd_command(ls)
    elif ls.startswith('adr_arith'): handle_adr_arith_hd_command(ls)
    elif ls.startswith('str'): handle_str_hd_command(ls)
    elif ls.startswith('dist.'): loader.dist_cmds.append((len(loader.result), ls[5:].strip(), getattr(loader, 'current_exec_info', {}))); loader.result.extend((0, 0))
    else:
        valid_commands = ['org', 'backup', 'call', 'def', '@def', 'lbl', 'func', 'repeat', 'loop', 'eval(', 'calc(', 'goto', 'goto_er14', 'goto_er6', 'adr(', 'pr_length', 'sizeof(', 'adr_of', 'adr_arith', 'str', 'dist.']
        valid_commands.extend(loader.commands.keys())
        valid_commands.extend(loader.datalabels.keys())
        valid_commands.extend(loader.vars_dict.keys())
        
        matches_full = difflib.get_close_matches(ls, valid_commands, n=1, cutoff=0.7)
        if matches_full:
            raise ValueError(f"Unrecognized command: {ls!r}. Did you mean {matches_full[0]!r}?")
        
        ls_first = ls.split()[0] if ls.split() else ls
        matches_first = difflib.get_close_matches(ls_first, valid_commands, n=1, cutoff=0.7)
        if matches_first:
            suggestion = matches_first[0] + ls[len(ls_first):]
            raise ValueError(f"Unrecognized command: {ls!r}. Did you mean {suggestion!r}?")
            
        raise ValueError(f'Unrecognized command: {ls!r}')
