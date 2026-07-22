import re
from libcompiler import utils
from libcompiler import loader
import difflib
from libcompiler.loader import sizeof_register, char_to_hex, token_to_hex
from libcompiler.i18n import t

sorted_tokens = sorted(token_to_hex.keys(), key=len, reverse=True)

def register_alias(name, target):
    if not hasattr(loader, 'aliases'):
        loader.aliases = {}
    loader.aliases[name] = target
    loader.aliases_pattern = None # Invalidate cache

def run_alias(line):
    if not hasattr(loader, 'aliases') or not loader.aliases:
        return line
    if not getattr(loader, 'aliases_pattern', None):
        pattern_str = r'\b(' + '|'.join(re.escape(k) for k in loader.aliases) + r')\b'
        loader.aliases_pattern = re.compile(pattern_str)
        
    parts = re.split(r'("[^"\\]*(?:\\.[^"\\]*)*"|\'[^\'\\]*(?:\\.[^\'\\]*)*\')', line)
    for i in range(0, len(parts), 2):
        parts[i] = loader.aliases_pattern.sub(lambda m: loader.aliases[m.group(1)], parts[i])
    return ''.join(parts)

def add_macro(pattern, rest, program_iter):
    if rest.startswith('{'):
        body_items, _ = collect_block_body(rest[1:], program_iter)
    else:
        body_items = [rest] if rest else []

    body_lines = [item[1] if isinstance(item, tuple) and len(item) == 2 else item.get("exec", str(item)) if isinstance(item, dict) else str(item) for item in body_items]

    canonical_pat = utils.canonicalize(pattern)
    converted_pat = re.escape(canonical_pat).replace(r"\<", "(?P<").replace("<", "(?P<").replace(r"\>", ">.+?)").replace(">", ">.+?)")
    
    keyword = pattern.split('<', 1)[0].strip()
    m_kw = re.match(r'^([a-zA-Z_]\w*)', keyword)
    macro_keyword = utils.canonicalize(m_kw.group(1) if m_kw else keyword.rstrip('(').strip())

    if not hasattr(loader, 'dynamic_macros'): loader.dynamic_macros = []
    loader.dynamic_macros.append({
        "pattern": pattern, "keyword": macro_keyword, "compiled_pattern": re.compile(converted_pat), "output": body_lines
    })
    loader.dynamic_macros.sort(key=lambda x: len(x["pattern"]), reverse=True)

def run_macro(line_strip, line_num, remaining_lines):
    if not hasattr(loader, 'dynamic_macros'): return False
    
    for macro in loader.dynamic_macros:
        if macro["keyword"] not in line_strip: continue
        match = macro["compiled_pattern"].search(line_strip)
        if match:
            local_env = match.groupdict()
            output_lines = []
            for out in macro["output"]:
                temp = out
                for k, v in local_env.items(): temp = temp.replace(f"<{k}>", str(v))
                output_lines.append(temp)
                
            if len(output_lines) == 1:
                replaced_line = line_strip[:match.start()] + output_lines[0] + line_strip[match.end():]
                remaining_lines.insert(0, (line_num, replaced_line))
            else:
                for out in reversed(output_lines):
                    remaining_lines.insert(0, (line_num, out))
            return True
    return False

def run_func(line_strip, raw_line, line_num, final_lines_to_process):
    m = re.match(r'(\w+)\s*\(((?:[^()]+|\([^()]*\))*)\)', line_strip)
    if not m or m.group(1) not in getattr(loader, "defined_functions", {}): return False
    
    called_func_name, call_args_str = m.group(1), m.group(2)
    func = loader.defined_functions[called_func_name]

    call_args = [arg.strip() for arg in re.findall(r'("(?:[^"\\]|\\.)*"|[^,]+)', call_args_str)]
    if call_args == [''] and not call_args_str: call_args = []

    params = func.get("params") or [(a, None) for a in func.get("args", [])]

    required = sum(1 for _, default in params if default is None)
    if len(call_args) > len(params) or len(call_args) < required:
        raise utils.CompilerError(t("err_args_mismatch_var0_7637", var0=line_strip))

    bound = list(call_args)
    for _, default in params[len(bound):]:
        bound.append(default)

    if "return_expr" in func:
        ret_expr = func["return_expr"]
        for (param, _), arg in zip(params, bound):
            parts = re.split(r'("[^"\\]*(?:\\.[^"\\]*)*"|\'[^\'\\]*(?:\\.[^\'\\]*)*\')', ret_expr)
            for i in range(0, len(parts), 2):
                parts[i] = re.sub(r'\b' + re.escape(param) + r'\b', arg, parts[i])
            ret_expr = ''.join(parts)
        final_lines_to_process.append({"exec": ret_expr, "raw": raw_line, "num": line_num, "ctx": f"inside '{called_func_name}'"})
        return True

    for (param, _), arg_val in zip(params, bound):
        if param.strip():
            final_lines_to_process.append({"exec": f"var {param.strip()} = {arg_val}", "raw": raw_line, "num": line_num, "ctx": f"passing args to '{called_func_name}'"})

    for item in func["body"]:
        f_line_num, line_in_func = item if isinstance(item, tuple) else (line_num, item)
        final_lines_to_process.append({"exec": line_in_func, "raw": line_in_func, "num": f_line_num, "ctx": f"inside '{called_func_name}'"})
    return True

def split_lines(line):
    if line.strip().startswith("@python"):
        return [line]
    parts, current, in_double, in_single = [], [], False, False
    for i, char in enumerate(line):
        if char == '"' and not in_single and (i == 0 or line[i-1] != '\\'): in_double = not in_double
        elif char == "'" and not in_double and (i == 0 or line[i-1] != '\\'): in_single = not in_single
        elif char == ';' and not in_double and not in_single:
            parts.append("".join(current).strip())
            current = []
            continue
        current.append(char)
    parts.append("".join(current).strip())
    return [p for p in parts if p]

def merge_lines(program_lines):
    final_merged, current_line, current_num, paren_depth = [], "", None, 0
    in_python_block, py_block, py_ln, py_depth = False, "", 0, 0
    
    for idx, item in enumerate(program_lines):
        line_num, raw_line = item if isinstance(item, tuple) else (idx + 1, item)
        
        if in_python_block:
            py_block += "\n" + raw_line
            r_strip = raw_line.strip()
            if not r_strip.startswith('#'):
                py_depth += r_strip.count('{') - r_strip.count('}')
            if py_depth <= 0:
                final_merged.append((py_ln, py_block))
                in_python_block = False
            continue
            
        if raw_line.strip().startswith('@python'):
            if current_line:
                final_merged.append((current_num, current_line.strip()))
                current_line, current_num, paren_depth = "", None, 0
            
            py_block = raw_line
            py_ln = line_num
            py_depth = 1 if '{' in raw_line else 0
            if '{' in raw_line and '}' in raw_line[raw_line.find('{')+1:]:
                final_merged.append((py_ln, py_block))
            else:
                if py_depth > 0: in_python_block = True
            continue
            
        comment_idx = raw_line.find('#')
        content = raw_line[:comment_idx] if comment_idx != -1 else raw_line
        
        # Merge trailing backslashes
        if content.rstrip().endswith('\\'):
            current_line += content[:content.rfind('\\')]
            current_num = current_num or line_num
            continue
            
        content_no_strings = re.sub(r'("[^"\\]*(?:\\.[^"\\]*)*"|\'[^\'\\]*(?:\\.[^\'\\]*)*\')', '', content)
        paren_depth += content_no_strings.count('(') - content_no_strings.count(')')
        
        current_line += (" " if current_line and paren_depth >= 0 else "") + content.strip()
        current_num = current_num or line_num
        
        if paren_depth <= 0:
            final_merged.append((current_num, current_line.strip()))
            current_line, current_num, paren_depth = "", None, 0

    if current_line: final_merged.append((current_num or len(program_lines), current_line.strip()))
    return final_merged

def parse_sections(program_lines):
    sections, current_name, current_lines = [], None, []

    for idx, item in enumerate(program_lines):
        ln, raw = item if isinstance(item, tuple) else (idx + 1, item)
        stripped = raw.strip()
        if stripped.startswith(('@set.', '@section.')):
            alias_name = None
            if ' as ' in stripped:
                stripped, alias_name = [x.strip() for x in stripped.rsplit(' as ', 1)]
            
            name_part, *addr_part = stripped.split("at", 1)
            if current_name is not None or current_lines: sections.append((current_name, current_lines))
            current_name = name_part.strip()[5:] if name_part.strip().startswith('@set.') else name_part.strip()[9:]
            
            if alias_name: register_alias(alias_name, current_name)
            
            current_lines = []
            if addr_part:
                org, *bkup = [x.strip() for x in addr_part[0].split("backup", 1)]
                if org: current_lines.append((ln, f"org {org}"))
                if bkup and bkup[0]: current_lines.append((ln, f"backup {bkup[0]}"))
        else: current_lines.append((ln, raw))
    if current_name is not None or current_lines: sections.append((current_name, current_lines))

    sections = [s for s in sections if s[0] is not None] + [s for s in sections if s[0] is None]
    return sections

def process_line(line, program_iter=None):
    line = line.strip()
    if not line or line.isspace(): return
    if line.startswith('/*'): loader.in_comment = True; return
    if '*/' in line: loader.in_comment = False; return
    if loader.in_comment: return

    if ';' in line:
        for cmd in line.split(';'): process_line(cmd.lower(), program_iter)
    else: dispatch_command_handler(line, program_iter)

def handle_fill_command(line):
    inner = line.strip()[5:-1].strip()
def _parse_two_args(inner):
    paren_balance = 0
    split_idx = -1
    for i, c in enumerate(inner):
        if c == '(': paren_balance += 1
        elif c == ')': paren_balance -= 1
        elif c == ',' and paren_balance == 0:
            split_idx = i
            break
            
    if split_idx == -1:
        return inner.strip(), "0"
        
    return inner[:split_idx].strip(), inner[split_idx+1:].strip()

def _eval_fill_args(expr1, expr2):
    eval_scope = {'pr_length': len(loader.result), **loader.vars_dict}
    
    for k in loader.labels:
        if k not in eval_scope: eval_scope[k] = k
    if hasattr(loader, 'global_labels'):
        for k in loader.global_labels:
            if k not in eval_scope: eval_scope[k] = k

    def pass1_adr(label, offset=0):
        if not isinstance(label, str): raise utils.CompilerError(t("err_label_must_be_str_c4b7", var0=type(label)))
        if label in loader.labels:
            return (loader.home or 0) + loader.labels[label] + offset
        if hasattr(loader, 'global_labels') and label in loader.global_labels:
            sec = getattr(loader, 'label_sections', {}).get(label)
            sec_home = 0
            if sec and hasattr(loader, 'section_addresses') and sec in loader.section_addresses:
                sec_home = loader.section_addresses[sec].get('org', 0)
            return sec_home + loader.global_labels[label] + offset
        raise utils.CompilerError(t("err_label_var0_not_found_45dc", var0=label))
        
    eval_scope['adr'] = pass1_adr
    
    def prepare_expr(expr):
        expanded = re.sub(r'\bpr_length\b', str(len(loader.result)), expr)
        if loader.vars_dict:
            pat = re.compile(r'\b(' + '|'.join(re.escape(k) for k in loader.vars_dict) + r')\b')
            expanded = pat.sub(lambda m: str(loader.vars_dict[m.group(1)]), expanded)
        return expanded
        
    val1 = int(utils.safe_eval(prepare_expr(expr1), eval_scope))
    val2 = int(utils.safe_eval(prepare_expr(expr2), eval_scope))
    return val1, val2

def _do_fill(count, value):
    if count < 0: raise utils.CompilerError(t("err_padding_count_cannot_be_daab", var0=count))
    if count == 0: return
    h = f"{value:x}"
    if len(h) % 2: h = '0' + h
    val = int(h, 16)
    byte_seq = []
    for _ in range(len(h) // 2):
        byte_seq.append(val & 0xFF)
        val >>= 8
    loader.result.extend(byte_seq * count)

def handle_fill_command(line):
    inner = line.strip()[5:-1].strip()
    expr1, expr2 = _parse_two_args(inner)
    count, value = _eval_fill_args(expr1, expr2)
    _do_fill(count, value)

def handle_align_command(line):
    inner = line.strip()[6:-1].strip()
    expr1, expr2 = _parse_two_args(inner)
    size, value = _eval_fill_args(expr1, expr2)
    if size <= 0: raise utils.CompilerError(t("err_align_size_must_be_da9e", var0=size))
    
    current_addr = (loader.home or 0) + len(loader.result)
    rem = current_addr % size
    count = (size - rem) % size
    _do_fill(count, value)

def handle_pad_command(line):
    is_abs = line.strip().startswith('pad_abs')
    inner = line.strip()[8:-1].strip() if is_abs else line.strip()[4:-1].strip()
    expr1, expr2 = _parse_two_args(inner)
    target, value = _eval_fill_args(expr1, expr2)
    
    if is_abs:
        if loader.home is None: raise utils.CompilerError(t("err_padabs_requires_section_origin_1660"))
        current_addr = loader.home + len(loader.result)
        count = target - current_addr
    else:
        count = target - len(loader.result)
        
    _do_fill(count, value)

def handle_label_definition(line):
    line_str = line.strip()
    label = line_str[4:].strip().lower() if line_str.lower().startswith('lbl ') else line_str[:-1].strip().lower()
    
    at_match = re.search(r'\s+at\s+(.+)$', label)
    if at_match:
        address_expr = at_match.group(1)
        label_name = label[:at_match.start()].strip()
        address = int(utils.safe_eval(address_expr))
        
        if label_name in loader.labels: raise utils.CompilerError(t("err_duplicate_label", label=label_name))
        if hasattr(loader, 'global_labels'):
            loader.global_labels[label_name] = address
            if getattr(loader, 'is_pass1', False):
                if not hasattr(loader, 'label_sections'): loader.label_sections = {}
                loader.label_sections[label_name] = getattr(loader, 'current_section_name', None)
            if not getattr(loader, 'is_pass1', False):
                utils.note(t("note_label_var0_is_at_1994", var0=label_name, var1=hex(address)))
        return

    if label in loader.labels: raise utils.CompilerError(t("err_duplicate_label", label=label))
    loader.labels[label] = len(loader.result)

def collect_block_body(first_line_rest, program_iter, line_num=None):
    if '}' in first_line_rest:
        content = first_line_rest[:first_line_rest.rfind('}')].strip()
        return ([(line_num, content)] if content and line_num is not None else [content] if content else []), True

    body_items, depth = [], 1
    if program_iter is None: raise utils.CompilerError(t("err_block_requires_an_iterator_09ba"))
        
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
    if not m: raise utils.CompilerError(t("err_invalid_func_syntax_var0_a35e", var0=line))
    func_name, args_str = m.group(1), m.group(2).strip()
    
    line_num = getattr(loader, 'current_line_num', None)
    body_items, _ = collect_block_body(line[m.end():].strip(), program_iter, line_num)
    
    body, return_expr = [], None
    for item in body_items:
        b_ln, content = item if isinstance(item, tuple) and len(item) == 2 else (item.get("num"), item.get("exec")) if isinstance(item, dict) else (line_num, str(item))
        stripped = content.strip()
        if not stripped: continue
        if stripped.startswith('return '):
            if return_expr is not None: raise utils.CompilerError(t("err_multiple_returns_in_var0_92b4", var0=func_name))
            return_expr = stripped[7:].strip()
        else:
            body.append((b_ln, stripped))
            
    if return_expr is not None and body: raise utils.CompilerError(t("err_function_var0_with_return_fe40", var0=func_name))
    # Parse each param: "name" or "name=default"
    params = []
    for a in (args_str.split(',') if args_str else []):
        a = a.strip()
        if '=' in a:
            pname, pdefault = [x.strip() for x in a.split('=', 1)]
            params.append((pname, pdefault))
        else:
            params.append((a, None))
    loader.defined_functions[func_name] = {"params": params, **({"return_expr": return_expr} if return_expr is not None else {"body": body})}

def execute_python_block(raw_block):
    if getattr(loader, 'safe_mode', False):
        if not getattr(loader, 'is_pass1', False):
            utils.note(t("note_warn_block_python_ignored_ea17"))
        return

    code_str = raw_block[raw_block.find('{')+1:raw_block.rfind('}')]
    import textwrap
    code_str = textwrap.dedent(code_str)
    
    env = {"loader": loader, "utils": utils}
    for k, v in loader.vars_dict.items():
        if isinstance(v, str):
            try: env[k] = int(v, 0)
            except ValueError: env[k] = v
        else: env[k] = v
    
    try:
        exec(code_str, env)
        for k, v in env.items():
            if k not in ["loader", "utils", "__builtins__"]:
                if isinstance(v, str):
                    if len(v) >= 2 and ((v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'"))):
                        loader.vars_dict[k] = v
                    else:
                        loader.vars_dict[k] = f'"{v}"'
                else:
                    loader.vars_dict[k] = str(v) if isinstance(v, int) else v
    except Exception as e:
        raise utils.CompilerError(t("err_error_executing_python_block_970c", var0=e))

def handle_python_block(line, program_iter):
    raw_block = getattr(loader, 'current_exec_info', {}).get('raw', '')
    execute_python_block(raw_block)

def handle_repeat_command(line, program_iter):
    m = re.match(r'(?:repeat|loop)\s+(.+?)\s*\{', line.strip())
    if not m: raise utils.CompilerError(t("err_invalid_repeat_syntax_var0_a977", var0=line))
    try: count = int(utils.safe_eval(m.group(1).strip(), loader.vars_dict.copy()))
    except Exception as e: raise utils.CompilerError(t("err_error_eval_repeat_count_3159", var0=m.group(1), var1=e))
        
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
    expanded_expr = re.sub(r'\bpr_org\((.*?)\)', lambda m: f'pr_org("{m.group(1).strip()}")', expanded_expr)
    expanded_expr = re.sub(r'\bpr_backup\((.*?)\)', lambda m: f'pr_backup("{m.group(1).strip()}")', expanded_expr)

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
    
    if 'adr(' in expanded_expr or 'sizeof(' in expanded_expr or 'dist.' in expanded_expr or 'pr_org(' in expanded_expr or 'pr_backup(' in expanded_expr:
        max_len = max([4] + [(len(m) + len(m)%2) for m in re.findall(r'\b0x([0-9a-fA-F]+)\b', expanded_expr)])
        max_bytes = max_len // 2
        loader.deferred_evals.append((len(loader.result), expanded_expr, getattr(loader, 'current_exec_info', {}), max_bytes))
        loader.result.extend([0] * max_bytes)
        return
        
    val = utils.safe_eval(expanded_expr, eval_scope)
    
    if isinstance(val, (int, list)):
        max_len = max([2] + [(len(m) + len(m)%2) for m in re.findall(r'\b0x([0-9a-fA-F]+)\b', expanded_expr)])
        for item in (val if isinstance(val, list) else [val]):
            process_line(f'0x{item:0{max_len}x}' if isinstance(item, int) else f'"{item}"')
    elif isinstance(val, str):
        process_line(f'"{val}"')
    else: raise utils.CompilerError(t("err_unsupported_eval_type_var0_4f9c", var0=type(val)))

def handle_list_command(line, program_iter):
    content = line[1:]

    if ']' in content:
        inner = content[:content.index(']')]
        process_line(inner) if inner.strip() else None
        return

    parts = []
    if content.strip():
        parts.append(content.strip())

    for item in program_iter:
        s = (item[1].strip() if isinstance(item, tuple)
             else item.get('exec', '').strip() if isinstance(item, dict)
             else str(item).strip())
        if not s:
            continue
        if ']' in s:
            before = s[:s.index(']')].strip().rstrip(';')
            if before:
                parts.append(before)
            break  # stop here — do NOT consume past ']'
        parts.append(s.rstrip(';'))

    cleaned = [p for p in parts if p]
    if cleaned:
        process_line(';'.join(cleaned))


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
            if matches: raise utils.CompilerError(t("err_call_target_not_found_a0d1", var0=cmd, var1=matches[0]))
            raise utils.CompilerError(t("err_call_target_not_found_1ae5", var0=cmd))
        adr, tags = loader.commands[cmd]
        for t in tags: 
            if t.startswith('warning'): utils.note(t + '\n')
            
    offset = 0
    if not getattr(loader, 'gadgets_offset_applied', False):
        try: 
            irange = loader.datalabels['input_range'] if 'input_range' in loader.datalabels else loader.datalabels['input_area']
            offset = 0x30300000 if loader.home and irange <= loader.home < irange + 0xc8 else 0
        except Exception:
            offset = 0x30300000
    
    process_line(f'0x{adr + offset:08x}')

def handle_goto_command(line):
    parts = line.split(maxsplit=1)
    if len(parts) < 2: raise utils.CompilerError(t("err_invalid_goto_syntax_var0_487b", var0=line))
    lbl = parts[1].lower()
    reg = 'er6' if line.startswith('goto_er6') else 'er14'
    process_line(f'{reg} = eval(adr("{lbl}") - 0x02);call sp={reg},pop {"er8" if reg=="er6" else reg}')

def handle_address_command(line):
    inner = line.strip()[4:-1].strip()
    parts = [p.strip() for p in inner.split(',')]
    if not parts or not parts[0] or len(parts) > 3: raise utils.CompilerError(t("err_invalid_adr_syntax_var0_b779", var0=line))
    
    expr = [f'adr("{parts[0]}")']
    if len(parts) > 1 and parts[1]: 
        expr.append(parts[1] if parts[1].startswith(('+','-')) else '+' + parts[1].replace(" ",""))
    if len(parts) > 2 and parts[2]:
        base_val = parts[2].replace(" ","")
        expr.append(f'+ {base_val} - homeof("{parts[0]}")')
        
    if len(expr) == 1:
        loader.deferred_evals.append((len(loader.result), expr[0], getattr(loader, 'current_exec_info', {})))
        loader.result.extend((0, 0))
    else: process_line(f'eval({" ".join(expr)})')

def handle_define_gadget_command(line):
    if ':' not in line: raise utils.CompilerError(t("err_invalid_def_syntax_var0_8aa9", var0=line))
    cmd, addr_str = [x.strip() for x in line[3:].strip().split(':', 1)]
    cmd = utils.canonicalize(cmd).lower()
    tags = []
    while cmd.startswith('{'):
        end = cmd.find('}')
        if end < 0: raise utils.CompilerError(t("err_unmatched_in_inline_def_a329", var0=line))
        tags.append(cmd[1:end])
        cmd = cmd[end+1:].strip()
    
    try:
        addr = int(addr_str, 16)
    except ValueError:
        raise utils.CompilerError(t("err_invalid_address_in_def_ba26", var0=addr_str))
    loader.add_command(loader.commands, addr, cmd, tags, 'inline def')
    utils.note(t("note_gadget_var0_is_var1_3172", var0=cmd, var1=addr_str))

def handle_assignment_command(line, program_iter):
    l, r = [x.strip() for x in line.split('=', 1)]
    
    m_func = re.match(r'^(\w+)\s*\(((?:[^()]+|\([^()]*\))*)\)$', r)
    if m_func and m_func.group(1) in getattr(loader, 'defined_functions', {}):
        f = loader.defined_functions[m_func.group(1)]
        if "return_expr" not in f: raise utils.CompilerError(t("err_func_var0_cannot_be_6345", var0=m_func.group(1)))
        args = [a.strip() for a in re.findall(r'("(?:[^"\\]|\\.)*"|[^,]+)', m_func.group(2))]
        if args == [''] and not m_func.group(2): args = []
        if len(args) != len(f["args"]): raise utils.CompilerError(t("err_args_mismatch_in_var0_f197", var0=r))
        r = f["return_expr"]
        for p, a in zip(f["args"], args):
            parts = re.split(r'("[^"\\]*(?:\\.[^"\\]*)*"|\'[^\'\\]*(?:\\.[^\'\\]*)*\')', r)
            for i in range(0, len(parts), 2):
                parts[i] = re.sub(r'\b' + re.escape(p) + r'\b', a, parts[i])
            r = ''.join(parts)

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
        var_name = l[4:].strip()
        loader.vars_dict[var_name] = r
        utils.note(t("note_variable_var0_set_to_08b0", var0=var_name, var1=r))
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
        if len(loader.result) - l1 != sizeof_register(reg): raise utils.CompilerError(t("err_line_var0_sourcedest_target_b481", var0=line))
    elif l.startswith("lbl "):
        process_line(l)
        process_line(r)
    else:
        loader.vars_dict[l] = r
        utils.note(t("note_variable_var0_set_to_08b0", var0=l, var1=r))

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
    text = m.group(1)
    
    def append_chars(content):
        for c in re.sub(r"\s", "~", content):
            try:
                hx = char_to_hex[c]
                if len(hx) == 2: loader.result.append(int(hx, 16))
                else: loader.result.extend([int(hx[:2], 16), int(hx[2:], 16)])
            except KeyError: raise utils.CompilerError(t("err_char_var0_not_found_282c", var0=c))

    # Scan for {expr} interpolations with balanced braces, supporting
    # arbitrary expressions: {name}, {name[0]}, {eval(name * 3)}, etc.
    last_idx = 0
    i = 0
    while i < len(text):
        if text[i] == '{':
            before = text[last_idx:i]
            if before: append_chars(before)
            # find the matching closing '}' with brace balancing
            depth, j = 1, i + 1
            while j < len(text) and depth > 0:
                if text[j] == '{': depth += 1
                elif text[j] == '}': depth -= 1
                j += 1
            expr = text[i+1:j-1].strip()
            if expr:
                # If already wrapped in eval/calc or contains operators/calls,
                # pass directly; otherwise wrap in eval() for variable lookup
                if re.match(r'^[a-zA-Z_]\w*(?:\[\d+\])?$', expr):
                    process_line(f"eval({expr})")
                else:
                    process_line(expr if expr.startswith(('eval(', 'calc(')) else f"eval({expr})")
            last_idx = j
            i = j
        else:
            i += 1

    after = text[last_idx:]
    if after: append_chars(after)

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
            if not hx: raise utils.CompilerError(t("err_unknown_token_var0_7e6d", var0=content[i]))
            if len(hx) == 2: loader.result.append(int(hx, 16))
            else: loader.result.extend([int(hx[:2], 16), int(hx[2:], 16)])
            i += 1

def handle_adr_of_hd_command(line):
    m = re.match(r'^adr_of\s*(?:\[(.*?)\]\s*)?(?:\[(.*?)\]\s*)?(\S+)$', line.strip())
    if not m: raise utils.CompilerError(t("err_invalid_adrof_syntax_var0_a410", var0=line))
    offset, base, lbl = m.group(1) or "+ 0", m.group(2), m.group(3)
    process_line(f'adr({lbl}, {offset.strip()}{f", {base}" if base else ""})')

def handle_adr_arith_hd_command(line):
    content = line.strip()[9:].strip()
    content = re.sub(r'\b(?:adr_arith|adr_of|adr)\b', '', content).strip()
    pairs = re.findall(r'(?:\[([^\]]+)\])?\s*([a-zA-Z_]\w*)', content)
    ops = [o[0] or o[1] for o in re.findall(r'\]\s*([+-])\s*(?:\[|\w)|(?:\s|[a-zA-Z_]\w*)\s*([+-])\s*(?:\[|[a-zA-Z_]\w*)', content)]
    if not pairs or len(pairs)-1 != len(ops): raise utils.CompilerError(t("err_invalid_adrarith_syntax_var0_f862", var0=line))
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
    if val is None: raise utils.CompilerError(t("err_invalid_str_syntax_var0_d4dd", var0=line))
    for c in re.sub(r"\s", "~", val):
        hx = char_to_hex[c]
        if len(hx) == 2: loader.result.append(int(hx, 16))
        else: loader.result.extend([int(hx[:2], 16), int(hx[2:], 16)])

def dispatch_command_handler(line, program_iter=None, defined_functions=None):
    ls = line.strip()
    if ls.startswith('org'):
        new_home = utils.safe_eval(ls[3:]) - len(loader.result)
        if loader.home is not None and loader.home != new_home: raise utils.CompilerError(t("err_inconsistent_value_of_home_174f"))
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
    elif ls.startswith('@python'): handle_python_block(ls, program_iter)
    elif (ls.lower().startswith('lbl ') or ":" in ls) and 'def' not in ls: handle_label_definition(ls)
    elif ls.startswith("func"): handle_function_definition(ls, program_iter)
    elif ls.startswith(("repeat", "loop")) and not ls.startswith('loop_'): handle_repeat_command(ls, program_iter)
    elif (ls.startswith('eval(') or ls.startswith('calc(')) and ls.endswith(')'): handle_eval_expression(ls)
    elif ls.startswith('fill(') and ls.endswith(')'): handle_fill_command(ls)
    elif ls.startswith('align(') and ls.endswith(')'): handle_align_command(ls)
    elif (ls.startswith('pad(') or ls.startswith('pad_abs(')) and ls.endswith(')'): handle_pad_command(ls)
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
    elif ls.startswith('pr_org(') or ls == 'pr_org()':
        m = re.match(r'^pr_org\((.*?)\)$', ls)
        sec = m.group(1).strip() if m and m.group(1).strip() else getattr(loader, 'current_section_name', None)
        loader.pr_org_cmds.append((len(loader.result), sec, getattr(loader, 'current_exec_info', {})))
        loader.result.extend((0, 0))
    elif ls.startswith('pr_backup(') or ls == 'pr_backup()':
        m = re.match(r'^pr_backup\((.*?)\)$', ls)
        sec = m.group(1).strip() if m and m.group(1).strip() else getattr(loader, 'current_section_name', None)
        loader.pr_backup_cmds.append((len(loader.result), sec, getattr(loader, 'current_exec_info', {})))
        loader.result.extend((0, 0))
    else:
        ls_first = ls.split()[0] if ls.split() else ls
        utils.check_keyword(ls_first)
        
        valid_commands = utils._SUGGESTION_KEYWORDS.copy()
        valid_commands.extend(loader.commands.keys())
        valid_commands.extend(loader.datalabels.keys())
        valid_commands.extend(loader.vars_dict.keys())
        
        matches_full = difflib.get_close_matches(ls, valid_commands, n=1, cutoff=0.7)
        if matches_full:
            raise utils.CompilerError(t("err_unrecognized_cmd", cmd=ls, suggestion=matches_full[0]))
        
        ls_first = ls.split()[0] if ls.split() else ls
        matches_first = difflib.get_close_matches(ls_first, valid_commands, n=1, cutoff=0.7)
        if matches_first:
            suggestion = matches_first[0] + ls[len(ls_first):]
            raise utils.CompilerError(t("err_unrecognized_cmd", cmd=ls, suggestion=suggestion))
            
        raise utils.CompilerError(t("err_unrecognized_cmd_no_sugg", cmd=ls))
