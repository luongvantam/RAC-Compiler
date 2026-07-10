import re
import os
import sys
import utils
import loader
from handlers import dispatch_command_handler, handle_function_definition

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
        from handlers import collect_block_body
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

    if len(call_args) != len(func["args"]): raise ValueError(f"Args mismatch: {line_strip}")

    if "return_expr" in func:
        ret_expr = func["return_expr"]
        for param, arg in zip(func["args"], call_args):
            parts = re.split(r'("[^"\\]*(?:\\.[^"\\]*)*"|\'[^\'\\]*(?:\\.[^\'\\]*)*\')', ret_expr)
            for i in range(0, len(parts), 2):
                parts[i] = re.sub(r'\b' + re.escape(param) + r'\b', arg, parts[i])
            ret_expr = ''.join(parts)
        final_lines_to_process.append({"exec": ret_expr, "raw": raw_line, "num": line_num, "ctx": f"inside '{called_func_name}'"})
        return True

    for param_def, arg_val in zip(func["args"], call_args):
        if param_def.strip():
            final_lines_to_process.append({"exec": f"var {param_def.strip()} = {arg_val}", "raw": raw_line, "num": line_num, "ctx": f"passing args to '{called_func_name}'"})
    
    for item in func["body"]:
        f_line_num, line_in_func = item if isinstance(item, tuple) else (line_num, item)
        final_lines_to_process.append({"exec": line_in_func, "raw": line_in_func, "num": f_line_num, "ctx": f"inside '{called_func_name}'"})
    return True

def split_lines(line):
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
    for idx, item in enumerate(program_lines):
        line_num, raw_line = item if isinstance(item, tuple) else (idx + 1, item)
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

def build_env():
    env = {k: int.from_bytes(bytes(v), 'little') if isinstance(v, list) else v for k, v in loader.vars_dict.items()}
    env.update({k: k for k in loader.labels if k not in env})
    if hasattr(loader, 'global_labels'):
        env.update({k: k for k in loader.global_labels if k not in env})

    def adr_eval(label, offset=0):
        if not isinstance(label, str): raise ValueError(f"Label must be str, got {type(label)}")
        if label == '$': return getattr(loader, 'current_pos', 0) + offset
        if label in loader.labels: return loader.labels[label] + offset
        if hasattr(loader, 'global_labels') and label in loader.global_labels: return loader.global_labels[label] + offset
        if getattr(loader, 'is_pass1', False): return 0
        raise ValueError(f'Label not found: {label}')

    def sizeof_eval(sec_name=""):
        if not sec_name or sec_name == getattr(loader, 'current_section_name', None): return len(loader.result)
        if hasattr(loader, 'section_addresses') and sec_name in loader.section_addresses: return loader.section_addresses[sec_name].get('length', 0)
        if getattr(loader, 'is_pass1', False): return 0
        raise ValueError(f"Section '{sec_name}' not found for sizeof calculation")

    def dist_eval(sec_name):
        sec = loader.section_addresses.get(sec_name, {}) if hasattr(loader, 'section_addresses') else {}
        org, backup = sec.get('org'), sec.get('backup')
        if sec_name == getattr(loader, 'current_section_name', None): org, backup = getattr(loader, 'home', None), getattr(loader, 'backup_address', None)
        if org is not None and backup is not None: return abs(backup - org) & 0xFFFF
        if getattr(loader, 'is_pass1', False): return 0
        raise ValueError(f"Section '{sec_name}' dist information missing")

    def homeof_eval(label):
        if label in loader.labels: return loader.home or 0
        if hasattr(loader, 'global_labels') and label in loader.global_labels:
            sec = getattr(loader, 'label_sections', {}).get(label)
            if sec and hasattr(loader, 'section_addresses') and sec in loader.section_addresses:
                return loader.section_addresses[sec].get('org', 0)
            return 0
        if getattr(loader, 'is_pass1', False): return 0
        raise ValueError(f"Home of label '{label}' not found")

    env.update({'adr': adr_eval, 'sizeof': sizeof_eval, 'dist': dist_eval, 'homeof': homeof_eval})
    return env

def eval_all():
    env, home_deps = build_env(), []
    temp_deferred = list(loader.deferred_evals)
    loader.deferred_evals.clear()

    for pos, expr, exec_info in temp_deferred:
        loader.current_pos = pos
        loader.current_exec_info = exec_info
        try:
            val = utils.safe_eval(expr, env)
        except Exception:
            try:
                temp_env = {k: utils.safe_eval(v[5:-1], env) if isinstance(v, str) and v.startswith("eval(") else v for k, v in env.items()}
                val = utils.safe_eval(expr, temp_env)
            except Exception as e:
                raise ValueError(f"Deferred eval error in {expr!r}: {e}")
        
        if not isinstance(val, int): raise ValueError(f"Eval {expr!r} not integer")
        
        is_abs = expr.count('adr(') > 1 or 'adr(' not in expr or any(l in loader.global_labels and l not in loader.labels for l in re.findall(r'adr\(\s*["\']?([a-zA-Z_0-9]+)', expr))
        if is_abs:
            val &= 0xFFFF
            if not getattr(loader, 'is_pass1', False) and any(loader.result[pos:pos+2]): print(f"[WARN] eval_abs overwrite at {pos:04X}")
            loader.result[pos], loader.result[pos + 1] = val & 0xFF, (val >> 8) & 0xFF
        else:
            home_deps.append((pos, val))
    return home_deps

def report_error(e, args):
    info = getattr(loader, 'current_exec_info', {})
    line_num, raw, ctx = info.get("num", "?"), info.get("raw", ""), info.get("ctx", "")
    fname = os.path.basename(args.input_file) if getattr(args, 'input_file', None) else "source".upper()
    
    is_tty = sys.stderr.isatty()
    if is_tty and sys.platform == 'win32':
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            h_err, mode = kernel32.GetStdHandle(-12), ctypes.c_ulong()
            if kernel32.GetConsoleMode(h_err, ctypes.byref(mode)): kernel32.SetConsoleMode(h_err, mode.value | 0x0004)
        except Exception: is_tty = False

    c_red, c_blu, c_bld, c_rst = ('\033[1;31m', '\033[1;34m', '\033[1m', '\033[0m') if is_tty else ('', '', '', '')
    caret = " " * (len(raw) - len(raw.lstrip())) + "^" * max(1, len(raw.strip()))
    pfx, arw = " " * (len(str(line_num)) + 1), " " * max(1, len(str(line_num)) - 2)

    sys.stderr.write(f"\n{c_red}{c_bld}error:{c_rst} {c_bld}{str(e)}{f' (inside {ctx})' if ctx else ''}{c_rst}\n")
    sys.stderr.write(f"{arw}{c_blu}-->{c_rst} {fname}:{line_num}\n{pfx}{c_blu}|{c_rst}\n")
    sys.stderr.write(f"{c_blu}{line_num} |{c_rst} {raw.rstrip()}\n{pfx}{c_blu}|{c_rst} {c_red}{caret}{c_rst}\n\n")
    sys.exit(1)

def set_memory(overflow_initial_sp, resolved_adr_cmds, home_deps):
    if loader.home is None:
        loader.home = overflow_initial_sp - loader.labels.get('home', 0)
        if loader.home + len(loader.result) > 0x8E00 and loader.current_section_name is None and not getattr(loader, 'is_pass1', False):
            utils.note(f'Warning: Program length after home = {len(loader.result)} bytes > {0x8E00 - loader.home} bytes\n')

    for s_adr, offset in resolved_adr_cmds + home_deps:
        t_adr = loader.home + offset
        if not getattr(loader, 'is_pass1', False) and any(loader.result[s_adr:s_adr+2]): print(f"[WARN] memory overwrite at {s_adr:04X}")
        loader.result[s_adr], loader.result[s_adr + 1] = t_adr & 0xFF, t_adr >> 8

    for lbl, offset in loader.labels.items():
        loader.global_labels[lbl] = loader.home + offset
        if not hasattr(loader, 'label_sections'): loader.label_sections = {}
        loader.label_sections[lbl] = loader.current_section_name
        if not getattr(loader, 'is_pass1', False): utils.note(f'Label {lbl} is at address {loader.home + offset:04X}\n')

    if loader.current_section_name:
        loader.section_addresses[loader.current_section_name] = {'org': loader.home, 'backup': loader.backup_address, 'length': len(loader.result)}

    for pos, sec, exec_info in loader.dist_cmds:
        loader.current_exec_info = exec_info
        if sec not in loader.section_addresses or loader.section_addresses[sec]['backup'] is None:
            if getattr(loader, 'is_pass1', False): continue
            raise ValueError(f"Section '{sec}' missing dist info")
        dist_val = abs(loader.section_addresses[sec]['backup'] - loader.section_addresses[sec]['org']) & 0xFFFF
        if not getattr(loader, 'is_pass1', False) and any(loader.result[pos:pos+2]): print(f"[WARN] dist overwrite at {pos:04X}")
        loader.result[pos], loader.result[pos+1] = dist_val & 0xFF, dist_val >> 8

def finish_math():
    for pos, l_off, l_lbl, r_off, r_lbl, op in loader.relocation_expressions:
        if l_lbl not in loader.labels or r_lbl not in loader.labels:
            if getattr(loader, 'is_pass1', False): continue
            raise ValueError(f'Label not found in adr: {l_lbl}, {r_lbl}')
        res = (loader.labels[l_lbl] + l_off + loader.labels[r_lbl] + r_off) if op == '+' else (loader.labels[l_lbl] + l_off - loader.labels[r_lbl] - r_off)
        res &= 0xFFFF
        if not getattr(loader, 'is_pass1', False) and any(loader.result[pos:pos+2]): print(f"[WARN] adr overwrite at {pos:04X}")
        loader.result[pos], loader.result[pos+1] = res & 0xFF, res >> 8

    for pos, sec, exec_info in getattr(loader, 'sizeof_cmds', []):
        loader.current_exec_info = exec_info
        val = len(loader.result) if not sec or sec == getattr(loader, 'current_section_name', None) else loader.section_addresses.get(sec, {}).get('length', 0) if hasattr(loader, 'section_addresses') and sec in loader.section_addresses else 0 if getattr(loader, 'is_pass1', False) else None
        if val is None: raise ValueError(f"Section '{sec}' not found for sizeof calculation")
        if not getattr(loader, 'is_pass1', False) and any(loader.result[pos:pos+2]): print(f"[WARN] sizeof overwrite at {pos:04X}")
        loader.result[pos], loader.result[pos+1] = val & 0xFF, val >> 8

    loader.relocation_expressions.clear()
    if hasattr(loader, 'sizeof_cmds'): loader.sizeof_cmds.clear()

def run_lines(args, program_lines, overflow_initial_sp):
    for attr in ('global_labels', 'section_addresses', 'label_sections'):
        if not hasattr(loader, attr): setattr(loader, attr, {})
    
    loader.result, loader.labels, loader.address_requests = [], {}, []
    loader.relocation_expressions, loader.deferred_evals, loader.dist_cmds = [], [], []
    loader.home, loader.backup_address, loader.in_comment = None, None, False
    loader.defined_functions, loader.dynamic_macros = {}, []

    class ProgramIterator:
        def __init__(self, items): self.items = items
        def __iter__(self): return self
        def __next__(self):
            if not self.items: raise StopIteration
            return self.items.pop(0)

    remaining_lines = [(ln, pt) for ln, ml in merge_lines(program_lines) for pt in split_lines(ml)]
    program_iter = ProgramIterator(remaining_lines)
    final_lines = []

    for line_num, raw_line in program_iter:
        loader.current_line_num = line_num
        line_strip = utils.canonicalize(utils.del_inline_comment(raw_line)).strip()
        if not line_strip: continue

        if line_strip.startswith("def") and "=>" in line_strip:
            pat, rest = raw_line.split('=>', 1)
            add_macro(pat[4:].strip() if pat.strip().startswith("def ") else pat.strip()[3:].strip(), rest.strip(), program_iter)
            continue

        if run_macro(line_strip, line_num, remaining_lines): continue

        m_alias = re.match(r'^(.+?)\s+as\s+([a-zA-Z_]\w*)$', line_strip)
        if m_alias and not line_strip.startswith(('"', "'")):
            register_alias(m_alias.group(2), m_alias.group(1).strip())
            continue

        raw_line = run_alias(raw_line)
        line = utils.canonicalize(utils.del_inline_comment(raw_line))
        if line.strip().startswith(('@set.', '@section.')):
            loader.current_section_name = (line.rsplit(' as ', 1)[0] if ' as ' in line else line).split()[0].split('.')[1]
            continue

        if line.strip().startswith("func "):
            handle_function_definition(line, program_iter)
            continue

        if run_func(line.strip(), raw_line, line_num, final_lines): continue
        final_lines.append({"exec": line, "raw": raw_line, "num": line_num, "ctx": ""})

    lines_iter = iter(final_lines)
    for item in lines_iter:
        l, raw, ln, ctx = (item["exec"], item["raw"], item["num"], item.get("ctx", "")) if isinstance(item, dict) else (item, item, "?", "")
        line_to_process = (utils.canonicalize(utils.del_inline_comment(run_alias(l)))).strip()
        if not line_to_process: continue
        if not line_to_process.startswith('"'): line_to_process = line_to_process.lower()

        note_log, orig_note = '', utils.note
        def local_note(st): nonlocal note_log; note_log += st
        utils.note = local_note

        loader.current_exec_info = {"line": line_to_process, "raw": raw, "num": ln, "ctx": ctx}
        try:
            process_line(line_to_process, lines_iter)
        except Exception as e:
            utils.note = orig_note
            report_error(e, args)

        utils.note = orig_note
        if note_log and not getattr(loader, 'is_pass1', False): utils.note(note_log)

    try:
        home_deps = eval_all()
        finish_math()

        resolved_adr = []
        for req in loader.address_requests:
            if len(req) == 4:
                s_adr, offset, target, exec_info = req
                loader.current_exec_info = exec_info
            else:
                s_adr, offset, target = req
            if target in loader.labels: resolved_adr.append((s_adr, loader.labels[target] + offset))
            elif target in loader.global_labels: resolved_adr.append((s_adr, loader.global_labels[target] - loader.home + offset))
            elif getattr(loader, 'is_pass1', False): resolved_adr.append((s_adr, 0))
            else: raise ValueError(f'Label not found: {target}')
        loader.address_requests.clear()

        set_memory(overflow_initial_sp, resolved_adr, home_deps)
    except Exception as e:
        report_error(e, args)

    if getattr(loader, 'is_pass1', False) or (loader.home == loader.home + len(loader.result) and loader.current_section_name is None): return None, None
    
    sys.stderr.write(utils.get_notes())
    print(f"=== {loader.home:#06x} -> {loader.home + len(loader.result):#06x}{f' ({loader.backup_address:#06x} -> {loader.backup_address + len(loader.result):#06x})' if loader.backup_address is not None else ''} ===")
    print(' '.join(f'{b:02x}' for b in loader.result))
    print('======')
    return loader.home, loader.result

def process_program(args, program_lines, overflow_initial_sp):
    loader.global_labels, loader.section_addresses, loader.label_sections, loader.aliases, loader.aliases_pattern = {}, {}, {}, {}, None
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
    
    if len(sections) == 1:
        loader.is_pass1, loader.current_section_name = False, sections[0][0]
        out_addr, out_bytes = run_lines(args, sections[0][1], overflow_initial_sp)
        return [(loader.current_section_name, out_addr, out_bytes)] if out_addr is not None else []

    loader.is_pass1 = True
    for name, lines in sections:
        loader.current_section_name = name
        run_lines(args, lines, overflow_initial_sp)

    loader.is_pass1, results = False, []
    for name, lines in sections:
        loader.current_section_name = name
        if name is not None: print(f"\n=== section @{name} ===")
        out_addr, out_bytes = run_lines(args, lines, overflow_initial_sp)
        if out_addr is not None: results.append((name, out_addr, out_bytes))

    loader.current_section_name = None
    return results

def process_line(line, program_iter=None):
    line = line.strip()
    if not line or line.isspace(): return
    if line.startswith('/*'): loader.in_comment = True; return
    if '*/' in line: loader.in_comment = False; return
    if loader.in_comment: return

    if ';' in line:
        for cmd in line.split(';'): process_line(cmd.lower(), program_iter)
    else: dispatch_command_handler(line, program_iter)
