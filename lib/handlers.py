import re
from .utils import to_lowercase
from . import utils
from . import loader
from .loader import sizeof_register, max_call_adr
def process_line(line, program_iter=None):
    from .engine import process_line as _process_line
    return _process_line(line, program_iter)
from .text import char_to_hex, token_to_hex

def handle_label_definition(line):
    """
    Syntax: lbl <label> or <label>:
    Special: If the label is 'home', it specifies the point to
    start program execution. By default it's at the begin.
    """
    label = to_lowercase(line.strip()[4:].strip()) if line.strip().lower().startswith('lbl ') else to_lowercase(line.strip()[:-1].strip())
    assert label not in loader.labels, f'Duplicate label: {label}'
    loader.labels[label] = len(loader.result)
    
def handle_function_definition(line, program_iter, defined_functions):
    m = re.match(r'func\s+(\w+)\s*\\((.*?)\\)\s*\\{', line.strip())
    if not m: raise ValueError(f"Invalid func definition syntax: {line}")
    func_name, args_str = m.group(1), m.group(2).strip()
    func_args = [arg.strip() for arg in args_str.split(',')] if args_str else []
    
    body = []
    for _, raw_line in program_iter:
        stripped = raw_line.split('---')[0].strip()
        if stripped == '}': break
        if stripped: body.append(stripped)
    defined_functions[func_name] = {"args": func_args, "body": body}

def handle_repeat_command(line, program_iter):
    """Syntax: repeat <expr> { <lines> }"""
    if line.startswith('repeat '):
        m = re.match(r'repeat\s+(.+?)\s*\\{', line.strip())
    elif line.startswith('loop '):
        m = re.match(r'loop\s+(.+?)\s*\\{', line.strip())
        
    if not m:
        raise ValueError(f"Invalid repeat syntax: {line}")
    count_expr = m.group(1).strip()
    try:
        eval_scope = loader.vars_dict.copy()
        count = utils.safe_eval(count_expr, eval_scope)
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
    
    # 1. Thay thế các biến thông thường từ loader.vars_dict
    for var_name, var_value in loader.vars_dict.items():
        pattern = r'\b' + re.escape(var_name) + r'\b'
        expanded_expr = re.sub(pattern, str(var_value), expanded_expr)

    # =========================================================================
    # 2. XỬ LÝ ĐỘNG DIST TRONG HÀM: Tìm và thay thế trực tiếp 'dist.<tên_section>'
    # =========================================================================
    def repl_dist(match):
        name = match.group(1)
        # Thử tìm trong bộ nhớ quản lý section chung
        if hasattr(loader, 'section_addresses') and name in loader.section_addresses:
            org = loader.section_addresses[name].get('org')
            backup = loader.section_addresses[name].get('backup')
            if org is not None and backup is not None:
                return str((backup - org) & 0xFFFF)
        
        # Dự phòng nếu là section hiện tại chưa kịp đẩy vào bộ nhớ chung
        if name == getattr(loader, 'current_section_name', None):
            org = getattr(loader, 'home', None)
            backup = getattr(loader, 'backup_address', None)
            if org is not None and backup is not None:
                return str((backup - org) & 0xFFFF)
                
        raise ValueError(f"Section '{name}' không tìm thấy thông tin org/backup để tính dist tại dòng: {line}")

    # Regex này tìm các chuỗi có dạng dist.abc hoặc dist.main_section
    expanded_expr = re.sub(r'\bdist\.(\w+)\b', repl_dist, expanded_expr)
    # =========================================================================

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
                    val = utils.safe_eval(inner_result, eval_scope)
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
    eval_scope['pr_length'] = len(loader.result)
    for k, v in loader.vars_dict.items():
        eval_scope[k] = v
        
    expanded_expr = eval_nested(expanded_expr, eval_scope)
    
    # Lúc này biểu thức đã được thay thế 'dist.main' thành số nguyên (ví dụ: 'adr(main)+55472')
    if 'adr(' in expanded_expr:
        loader.deferred_evals.append((len(loader.result), expanded_expr))
        loader.result.extend((0, 0))
        return
        
    eval_scope = {}
    eval_scope['pr_length'] = len(loader.result)
    try:
        val = utils.safe_eval(expanded_expr, eval_scope)
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

def handle_list_command(line, program_iter):
    if line.startswith('['):
        content = line[1:]
        if ']' in content:
            content = content.split(']')[0]
        else:
            parts = [content]
            for item in program_iter:
                current = item[1] if isinstance(item, tuple) else item.get("exec") if isinstance(item, dict) else str(item)
                s = current.strip()
                if not s:
                    continue
                if ']' in s:
                    parts.append(s.split(']')[0])
                    break
                parts.append(s)
            content = "\n".join(parts)
        line = content.replace('\n', ';')
        process_line(line)

def handle_hex_data(line):
    """Syntax: 
        0x<hex_digits>
        hex <hex_digits_reversed>
    """
    if line.startswith('0x'):
        hex_str = line[2:]
        if len(hex_str) % 2 != 0:
            hex_str = '0' + hex_str
        n_byte = len(hex_str) // 2
        data = int(hex_str, 16)
        for _ in range(n_byte):
            loader.result.append(data & 0xFF)
            data >>= 8
    elif line.startswith('hex'):
        data_str = line[3:].strip()
        assert len(data_str.replace(" ", "")) % 2 == 0, f'Invalid data length'
        data_bytes = bytes.fromhex(data_str)
        loader.result.extend(data_bytes)

def handle_call_command(line):
    """Syntax: `call <address>` or `call <built-in>`."""
    try:
        adr = int(line[4:], 16)
    except ValueError:
        func_name = line[4:].strip()
        adr, tags = loader.commands[func_name]
        for tag in tags:
            if tag.startswith('warning'):
                utils.note(tag + '\n')

    assert 0 <= adr <= max_call_adr, f'Invalid address: {adr}'
    try:
        input_range = loader.datalabels['input_range'] if 'input_range' in loader.datalabels else loader.datalabels['input_area']
        if loader.home >= input_range and loader.home < input_range + 0xc8:
            process_line(f'0x{adr + 0x30300000:0{8}x}')
        else:
            process_line(f'0x{adr + 0x00000000:0{8}x}')
    except TypeError:
        process_line(f'0x{adr + 0x30300000:0{8}x}')

def handle_goto_command(line):
    """Syntax: `goto <label>`"""
    label = to_lowercase(line[4:])
    process_line(f'er14 = eval(adr({label}) - 0x02);call sp=er14,pop er14')

def handle_address_command(line):
    line_strip = line.strip()
    if line_strip.startswith('adr(') and line_strip.endswith(')'):
        inner_content = line_strip[4:-1].strip()
        
        pattern = r'^([a-zA-Z_]\w*)(?:\s*,\s*([+-]?\s*(?:0x[0-9a-fA-F]+|\w+)))?(?:\s*,\s*([+-]?\s*(?:0x[0-9a-fA-F]+|\w+)))?$'
        match = re.match(pattern, inner_content)
        if not match:
            raise ValueError(f"Invalid adr(...) syntax: {line}")
            
        label_name = match.group(1)
        offset_part = match.group(2)
        base_addr_part = match.group(3)
        
        offset_str = "+ 0"
        if offset_part:
            offset_part = offset_part.replace(" ", "")
            if not offset_part.startswith('+') and not offset_part.startswith('-'):
                offset_str = f"+ {offset_part}"
            else:
                offset_str = f"{offset_part[0]} {offset_part[1:].strip()}"
                
        if base_addr_part:
            base_addr_part = base_addr_part.replace(" ", "")
            if base_addr_part.startswith('0x') or base_addr_part.startswith('0X'):
                base_addr_val = int(base_addr_part, 16)
            else:
                base_addr_val = int(base_addr_part)
                
            current_home = loader.home if loader.home is not None else 0
            distance = base_addr_val - current_home
            
            if distance >= 0:
                expr = f'eval(adr("{label_name}") + {distance} {offset_str})'
            else:
                expr = f'eval(adr("{label_name}") - {abs(distance)} {offset_str})'
            process_line(expr)
        else:
            if offset_part:
                expr = f'eval(adr("{label_name}") {offset_str})'
                process_line(expr)
            else:
                expr = f'adr("{label_name}")'
            
                loader.deferred_evals.append((len(loader.result), expr))
                loader.result.extend((0, 0))
    else:
        raise ValueError(f"Unrecognized adr command: {line}")

def handle_data_label(line):
    """`<label>`."""
    line = loader.datalabels[line.strip()]
    process_line(f'0x{line:x}')

def handle_builtin_command(line):
    """`<built-in>`. Equivalent to `call <built-in>`."""
    line = to_lowercase(line)
    process_line('call ' + line)

def handle_assignment_command(line, program_iter):
    i = line.index('=')
    left, right = line[:i].strip(), line[i+1:].strip()
    
    if right.startswith('['):
        content = right[1:]
        if ']' in content:
            content = content.split(']')[0]
        else:
            parts = [content] if content.strip() else []
            for item in program_iter:
                current = item[1] if isinstance(item, tuple) else item.get("exec") if isinstance(item, dict) else str(item)
                s = current.strip()
                if not s:
                    continue
                if ']' in s:
                    parts.append(s.split(']')[0])
                    break
                parts.append(s)
            content = "\n".join(parts)
        right = content.replace('\n', ';')

    if left.startswith("var "):
        var_name = left[4:].strip()
        val = right
        loader.vars_dict[var_name] = val
        utils.note(f"Variable '{var_name}' set to: {val}\n")
    elif left.startswith("reg ") or (left[0] in 'rexq' and any(left.startswith(prefix) for prefix in ['r', 'er', 'xr', 'qr', 'ea'])):
        register = left[4:].strip() if left.startswith("reg ") else left
        right = right.lower()
        new_right = []
        paren_balance = 0
        for char in right:
            if char == '(':paren_balance += 1
            elif char == ')':paren_balance -= 1
            if char == ',' and paren_balance == 0:new_right.append(';')
            else:new_right.append(char)
        value = "".join(new_right)
        process_line(f'call pop {register}')
        l1 = len(loader.result)
        process_line(value)
        assert len(loader.result) - l1 == sizeof_register(register), f'Line {line!r} source/destination target mismatches'
    else:
        val = right
        loader.vars_dict[left] = val
        utils.note(f"Variable '{left}' set to: {val}\n")

def resolve_index(value, index):
    value = str(value).strip()
    if value.startswith('"') and value.endswith('"'):
        inner = value[1:-1]
        return f'"{inner[index]}"' if 0 <= index < len(inner) else ''
    if ';' in value:
        items = [x.strip() for x in value.split(';') if x.strip()]
        return items[index] if 0 <= index < len(items) else ''
    return value

def handle_variable_expansion(line):
    expanded = line
    def replace_index(match):
        var_name = match.group(1)
        index = int(match.group(2))
        if var_name in loader.vars_dict:
            return str(resolve_index(loader.vars_dict[var_name], index))
        return match.group(0)
    expanded = re.sub(r'\b(\w+)\[(\d+)\]', replace_index, expanded)
    def replace_var(match):
        var_name = match.group(0)
        if var_name in loader.vars_dict:
            return str(loader.vars_dict[var_name])
        return var_name
    expanded = re.sub(r'\b\w+\b', replace_var, expanded)
    process_line(expanded)

def handle_org_command(line):
    ''' Syntax: `org <expr>`
    Specify the address of this location after mapping.
    Only use this for loader mode.
    '''
    hx = int(line[3:], 0)
    new_home = hx - len(loader.result)
    assert loader.home is None or loader.home == new_home, 'Inconsistent value of `home`'
    loader.home = new_home

def handle_backup_command(line):
    """Syntax: backup <expr>"""
    expr = line[6:].strip()
    try:
        eval_scope = loader.vars_dict.copy()
        #val = eval(expr, {}, eval_scope)
        val = int(expr, 0)
        if not isinstance(val, int):
             raise ValueError(f"Backup address must evaluate to an integer, got {type(val)}")
        loader.backup_address = val
    except Exception as e:
        raise ValueError(f"Error evaluating backup address '{expr}': {e}")

def handle_pr_length_command(line):
    ''' Syntax: `pr_length`
    Defers the calculation of the program length until the end of processing.
    '''
    loader.pr_length_cmds.append(len(loader.result))
    loader.result.extend((0, 0))

def handle_string_command(line):
    line_strip = line.strip()
    match = re.search(r'"(.*)"', line_strip)
    if not match:
        return
    content = match.group(1)
    def replace_calc(m):
        return process_line(f"eval({m.group(1)})") or ''
    content = re.sub(r'\{([a-zA-Z_]\w*(?:\[\d+\])?)\}', replace_calc, content)
    content = content.encode("latin1").decode("utf-8")
    utils.note(f"Processing string: {content.replace('~', ' ')}\n")
    processed_text = re.sub(r"\s", "~", content)
    for c in processed_text:
        try:
            hex_val = char_to_hex[c]
            if len(hex_val) == 2:
                loader.result.append(int(hex_val, 16))
            elif len(hex_val) == 4:
                loader.result.extend([int(hex_val[:2], 16), int(hex_val[2:], 16)])
        except KeyError:
            raise ValueError(f"Character '{c}' not found in conversion table")
        
def handle_token_literal(line):
    content = line[1:-1].strip()
    content = content.replace(" ", "")
    utils.note(f"Processing token sequence: {content}\n")
    sorted_tokens = sorted(token_to_hex.keys(), key=len, reverse=True)
    tokens = []
    i = 0
    while i < len(content):
        for t in sorted_tokens:
            if content.startswith(t, i):
                tokens.append(t)
                i += len(t)
                break
        else:
            tokens.append(content[i])
            i += 1
    for t in tokens:
        if t in token_to_hex:
            hex_val = token_to_hex[t]

            if len(hex_val) == 2:
                loader.result.append(int(hex_val, 16))
            elif len(hex_val) == 4:
                loader.result.extend([
                    int(hex_val[:2], 16),
                    int(hex_val[2:], 16)
                ])
        else:
            raise ValueError(f"Unknown token/char: {t}")

def handle_adr_of_hd_command(line):
    line_strip = line.strip()
    if not line_strip.startswith('adr_of'):
        raise ValueError(f"Unrecognized adr_of command: {line}")
    content = line_strip[6:].strip()
    match = re.match(r'^(?:\[(.*?)\])?\s*(\S+)$', content)
    if not match:
        raise ValueError(f"Invalid adr_of syntax: {line}")
    offset_part = match.group(1)
    label_name = match.group(2)
    offset_part = "+ 0" if offset_part is None else offset_part.strip()
    expr = f'adr({label_name}, {offset_part})'
    process_line(expr)

def handle_adr_arith_hd_command(line):
    line_strip = line.strip()
    if not line_strip.startswith('adr_arith'):
        raise ValueError(f"Unrecognized adr_arith command: {line}")
    content = line_strip[9:].strip()
    content = re.sub(r'\badr_arith\b', '', content).strip()
    pattern = r'(?:\[([^\]]+)\])?\s*([a-zA-Z_]\w*)'
    pairs = re.findall(pattern, content)
    operators = re.findall(r'\]\s*([+-])\s*(?:\[|\w)|(?:\s|[a-zA-Z_]\w*)\s*([+-])\s*(?:\[|[a-zA-Z_]\w*)', content)
    operators = [op[0] or op[1] for op in operators]
    if not pairs or (len(pairs) - 1 != len(operators)):
        raise ValueError(f"Invalid adr_arith syntax: {line}")
    expr_parts = []
    for i, (offset, label) in enumerate(pairs):
        sub_expr = f'adr("{label}")'
        if offset:
            offset = offset.strip()
            if not offset.startswith('+') and not offset.startswith('-'):
                sub_expr += f' {offset[0]} {offset[1:].strip()}'
        else:
            sub_expr += ' + 0'
        expr_parts.append(f'({sub_expr})')
        if i < len(operators):
            expr_parts.append(operators[i])
    expr = ' '.join(expr_parts)
    process_line(f'eval({expr})')

def handle_str_hd_command(line):
    line_strip = line.strip()
    if not line_strip.startswith('str'):
        raise ValueError(f"Unrecognized str command: {line}")
        
    content = line_strip[3:].strip()
    
    def encode_and_process_string(string_val):
        string_val = string_val.encode("latin1").decode("utf-8")
        processed_text = re.sub(r"\s", "~", string_val)
        for c in processed_text:
            try:
                hex_val = char_to_hex[c]
                if len(hex_val) == 2:
                    loader.result.append(int(hex_val, 16))
                elif len(hex_val) == 4:
                    loader.result.extend([int(hex_val[:2], 16), int(hex_val[2:], 16)])
            except KeyError:
                raise ValueError(f"Character '{c}' not found in conversion table")

    match_var_str = re.match(r'^([a-zA-Z_]\w*)\s+"([^"]*)"$', content)
    if match_var_str:
        var_name = match_var_str.group(1)
        string_val = match_var_str.group(2)
        loader.vars_dict[var_name] = string_val
        utils.note(f"Variable '{var_name}' set to string: {string_val}\n")
        return

    match_str_only = re.match(r'^"([^"]*)"$', content)
    if match_str_only:
        string_val = match_str_only.group(1)
        utils.note(f"Processing string: {string_val}\n")
        encode_and_process_string(string_val)
        return

    match_var_only = re.match(r'^([a-zA-Z_]\w*)$', content)
    if match_var_only:
        var_name = match_var_only.group(1)
        if var_name not in loader.vars_dict:
            raise ValueError(f"Variable '{var_name}' not found in vars_dict")
        
        string_val = str(loader.vars_dict[var_name])
        utils.note(f"Processing string from variable '{var_name}': {string_val}\n")
        encode_and_process_string(string_val)
        return

    raise ValueError(f"Invalid str syntax: {line}")

def handle_dist_command(line):
    """Syntax: dist.<section_name>"""
    section_name = line[5:].strip()
    if not section_name:
        raise ValueError("Invalid dist syntax: missing section name")
    loader.dist_cmds.append((len(loader.result), section_name))
    loader.result.extend((0, 0))

def dispatch_command_handler(line, program_iter=None, defined_functions=None):
    line_strip = line.strip()
    if line_strip.lower().startswith('lbl ') or ":" in line_strip:
        handle_label_definition(line)

    elif line_strip.startswith("func "):
        if program_iter is None or defined_functions is None:
            raise ValueError("Function handling requires program_iter and defined_functions")
        handle_function_definition(line, program_iter, defined_functions)

    elif line_strip.startswith("repeat ") or line_strip.startswith("loop "):
        if program_iter is None:
            raise ValueError("Repeat handling requires program_iter")
        handle_repeat_command(line, program_iter)

    elif line.startswith('0x') or (line.startswith('hex') and 'hex_' not in line):
        handle_hex_data(line)

    elif (line.startswith('eval(') or line.startswith('calc(')) and line.endswith(')'):
        handle_eval_expression(line)

    elif line.startswith('call'):
        handle_call_command(line)

    elif line.startswith('goto'):
        handle_goto_command(line)

    elif line.startswith('adr('):
        handle_address_command(line)

    elif line in loader.datalabels:
        handle_data_label(line)

    elif line in loader.commands:
        handle_builtin_command(line)

    elif re.match(r'^\w+(\[\d+\])?$', line) and re.match(r'^\w+', line).group(0) in loader.vars_dict:
        handle_variable_expansion(line)

    elif '=' in line:
        handle_assignment_command(line, program_iter)

    elif line.startswith('org'):
        handle_org_command(line)

    elif line.startswith('pr_length'):
        handle_pr_length_command(line)

    elif line_strip.startswith('"'):
        handle_string_command(line_strip)

    elif line_strip.startswith("'"):
        handle_token_literal(line_strip)

    elif line_strip.startswith('['):
        if program_iter is None:
            raise ValueError("List handling requires program_iter")
        handle_list_command(line, program_iter)

    elif line_strip.startswith('adr_of'):
        handle_adr_of_hd_command(line_strip)
    
    elif line_strip.startswith('adr_arith'):
        handle_adr_arith_hd_command(line_strip)
    
    elif line_strip.startswith('str'):
        handle_str_hd_command(line_strip)

    elif line_strip.startswith('backup '):
        handle_backup_command(line_strip)

    elif line_strip.startswith('dist.'):
        handle_dist_command(line_strip)

    else:
        assert False, f'Unrecognized command: {line!r}'