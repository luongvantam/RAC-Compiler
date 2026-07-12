import re
import os
import sys
import utils
import loader
import handlers

def build_env():
    env = {k: int.from_bytes(bytes(v), 'little') if isinstance(v, list) else v for k, v in loader.vars_dict.items()}
    env.update({k: k for k in loader.labels if k not in env})
    if hasattr(loader, 'global_labels'):
        env.update({k: k for k in loader.global_labels if k not in env})

    def adr_eval(label, offset=0):
        if not isinstance(label, str): raise utils.CompilerError(f"Label must be str, got {type(label)}")
        if label == '$': return getattr(loader, 'current_pos', 0) + offset
        if label in loader.labels: return loader.labels[label] + offset
        if hasattr(loader, 'global_labels') and label in loader.global_labels: return loader.global_labels[label] + offset
        if getattr(loader, 'is_pass1', False): return 0
        raise utils.CompilerError(f'Label not found: {label}')

    def sizeof_eval(sec_name=""):
        if not sec_name or sec_name == getattr(loader, 'current_section_name', None): return len(loader.result)
        if hasattr(loader, 'section_addresses') and sec_name in loader.section_addresses: return loader.section_addresses[sec_name].get('length', 0)
        if getattr(loader, 'is_pass1', False): return 0
        raise utils.CompilerError(f"Section '{sec_name}' not found for sizeof calculation")

    def dist_eval(sec_name):
        sec = loader.section_addresses.get(sec_name, {}) if hasattr(loader, 'section_addresses') else {}
        org, backup = sec.get('org'), sec.get('backup')
        if sec_name == getattr(loader, 'current_section_name', None): org, backup = getattr(loader, 'home', None), getattr(loader, 'backup_address', None)
        if org is not None and backup is not None: return abs(backup - org) & 0xFFFF
        if getattr(loader, 'is_pass1', False): return 0
        raise utils.CompilerError(f"Section '{sec_name}' dist information missing")

    def homeof_eval(label):
        if label in loader.labels: return loader.home or 0
        if hasattr(loader, 'global_labels') and label in loader.global_labels:
            sec = getattr(loader, 'label_sections', {}).get(label)
            if sec and hasattr(loader, 'section_addresses') and sec in loader.section_addresses:
                return loader.section_addresses[sec].get('org', 0)
            return 0
        if getattr(loader, 'is_pass1', False): return 0
        raise utils.CompilerError(f"Home of label '{label}' not found")

    def pr_org_eval(sec_name=""):
        sec = loader.section_addresses.get(sec_name, {}) if hasattr(loader, 'section_addresses') else {}
        org = sec.get('org')
        if not sec_name or sec_name == getattr(loader, 'current_section_name', None): org = getattr(loader, 'home', None)
        if org is not None: return org & 0xFFFF
        if getattr(loader, 'is_pass1', False): return 0
        raise utils.CompilerError(f"Section '{sec_name}' org information missing")

    def pr_backup_eval(sec_name=""):
        sec = loader.section_addresses.get(sec_name, {}) if hasattr(loader, 'section_addresses') else {}
        backup = sec.get('backup')
        if not sec_name or sec_name == getattr(loader, 'current_section_name', None): backup = getattr(loader, 'backup_address', None)
        if backup is not None: return backup & 0xFFFF
        if getattr(loader, 'is_pass1', False): return 0
        raise utils.CompilerError(f"Section '{sec_name}' backup information missing")

    env.update({'adr': adr_eval, 'sizeof': sizeof_eval, 'dist': dist_eval, 'homeof': homeof_eval, 'pr_org': pr_org_eval, 'pr_backup': pr_backup_eval})
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
                raise utils.CompilerError(f"Deferred eval error in {expr!r}: {e}")
        
        if not isinstance(val, int): raise utils.CompilerError(f"Eval {expr!r} not integer")
        
        is_abs = expr.count('adr(') > 1 or 'adr(' not in expr or any(l in loader.global_labels and l not in loader.labels for l in re.findall(r'adr\(\s*["\']?([a-zA-Z_0-9]+)', expr))
        if is_abs:
            val &= 0xFFFF
            if not getattr(loader, 'is_pass1', False) and any(loader.result[pos:pos+2]): print(f"[WARN] eval_abs overwrite at {pos:04X}")
            loader.result[pos], loader.result[pos + 1] = val & 0xFF, (val >> 8) & 0xFF
        else:
            home_deps.append((pos, val))
    return home_deps


def configure_memory_layout(base_sp, addr_resolution_list, dependencies):
    # Determine base address
    if loader.home is None:
        loader.home = base_sp - loader.labels.get('home', 0)
        # Validate output boundaries
        is_final_pass = not getattr(loader, 'is_pass1', False)
        if is_final_pass and loader.current_section_name is None:
            max_size = 0x8E00 - loader.home
            current_size = len(loader.result)
            if current_size > max_size:
                utils.note(f"[WARN] Total length after home = {current_size} bytes > {max_size} bytes\n")

    is_final_pass = not getattr(loader, 'is_pass1', False)
    
    # Apply compiled offsets
    all_memory_requests = addr_resolution_list + dependencies
    for index, off in all_memory_requests:
        target = loader.home + off
        if is_final_pass and any(loader.result[index:index+2]): 
            utils.note(f"[WARN] Memory overwrite at {index:04X} -> {target:04X}\n")
        
        loader.result[index] = target & 0xFF
        loader.result[index + 1] = target >> 8

    # Export mapping for global usage
    if not hasattr(loader, 'label_sections'):
        loader.label_sections = {}
        
    for sym_name, sym_offset in loader.labels.items():
        abs_addr = loader.home + sym_offset
        loader.global_labels[sym_name] = abs_addr
        loader.label_sections[sym_name] = loader.current_section_name
        
        if is_final_pass:
            utils.note(f'Label {sym_name} is at address {abs_addr:04X}\n')

    # Record chunk coordinates
    active_section = loader.current_section_name
    if active_section:
        loader.section_addresses[active_section] = {
            'org': loader.home,
            'backup': loader.backup_address,
            'length': len(loader.result)
        }

    # Resolve delta computations
    for index, sec_key, exec_ctx in loader.dist_cmds:
        loader.current_exec_info = exec_ctx
        
        sec_data = loader.section_addresses.get(sec_key)
        if not sec_data or sec_data.get('backup') is None:
            if not is_final_pass:
                continue
            raise utils.CompilerError(f"Missing section reference '{sec_key}'")
            
        delta = abs(sec_data['backup'] - sec_data['org']) & 0xFFFF
        
        if is_final_pass and any(loader.result[index:index+2]):
            print(f"[WARN] delta clash at {index:04X}")
            
        loader.result[index] = delta & 0xFF
        loader.result[index+1] = delta >> 8

def finish_math():
    for pos, l_off, l_lbl, r_off, r_lbl, op in loader.relocation_expressions:
        if l_lbl not in loader.labels or r_lbl not in loader.labels:
            if getattr(loader, 'is_pass1', False): continue
            raise utils.CompilerError(f'Label not found in adr: {l_lbl}, {r_lbl}')
        res = (loader.labels[l_lbl] + l_off + loader.labels[r_lbl] + r_off) if op == '+' else (loader.labels[l_lbl] + l_off - loader.labels[r_lbl] - r_off)
        res &= 0xFFFF
        if not getattr(loader, 'is_pass1', False) and any(loader.result[pos:pos+2]): print(f"[WARN] adr overwrite at {pos:04X}")
        loader.result[pos], loader.result[pos+1] = res & 0xFF, res >> 8

    for pos, sec, exec_info in getattr(loader, 'sizeof_cmds', []):
        loader.current_exec_info = exec_info
        val = len(loader.result) if not sec or sec == getattr(loader, 'current_section_name', None) else loader.section_addresses.get(sec, {}).get('length', 0) if hasattr(loader, 'section_addresses') and sec in loader.section_addresses else 0 if getattr(loader, 'is_pass1', False) else None
        if val is None: raise utils.CompilerError(f"Section '{sec}' not found for sizeof calculation")
        if not getattr(loader, 'is_pass1', False) and any(loader.result[pos:pos+2]): print(f"[WARN] sizeof overwrite at {pos:04X}")
        loader.result[pos], loader.result[pos+1] = val & 0xFF, val >> 8

    for pos, sec, exec_info in getattr(loader, 'pr_org_cmds', []):
        loader.current_exec_info = exec_info
        val = loader.home if not sec or sec == getattr(loader, 'current_section_name', None) else loader.section_addresses.get(sec, {}).get('org') if hasattr(loader, 'section_addresses') and sec in loader.section_addresses else 0 if getattr(loader, 'is_pass1', False) else None
        if val is None: raise utils.CompilerError(f"Section '{sec}' not found for pr_org calculation")
        if not getattr(loader, 'is_pass1', False) and any(loader.result[pos:pos+2]): print(f"[WARN] pr_org overwrite at {pos:04X}")
        loader.result[pos], loader.result[pos+1] = val & 0xFF, (val >> 8) & 0xFF

    for pos, sec, exec_info in getattr(loader, 'pr_backup_cmds', []):
        loader.current_exec_info = exec_info
        val = loader.backup_address if not sec or sec == getattr(loader, 'current_section_name', None) else loader.section_addresses.get(sec, {}).get('backup') if hasattr(loader, 'section_addresses') and sec in loader.section_addresses else 0 if getattr(loader, 'is_pass1', False) else None
        if val is None: raise utils.CompilerError(f"Section '{sec}' not found for pr_backup calculation")
        if not getattr(loader, 'is_pass1', False) and any(loader.result[pos:pos+2]): print(f"[WARN] pr_backup overwrite at {pos:04X}")
        loader.result[pos], loader.result[pos+1] = val & 0xFF, (val >> 8) & 0xFF

    loader.relocation_expressions.clear()
    if hasattr(loader, 'sizeof_cmds'): loader.sizeof_cmds.clear()
    if hasattr(loader, 'pr_org_cmds'): loader.pr_org_cmds.clear()
    if hasattr(loader, 'pr_backup_cmds'): loader.pr_backup_cmds.clear()

def run_lines(args, program_lines, overflow_initial_sp):
    for attr in ('global_labels', 'section_addresses', 'label_sections'):
        if not hasattr(loader, attr): setattr(loader, attr, {})
    
    loader.result, loader.labels, loader.address_requests = [], {}, []
    loader.relocation_expressions, loader.deferred_evals, loader.dist_cmds, loader.pr_org_cmds, loader.pr_backup_cmds = [], [], [], [], []
    loader.home, loader.backup_address, loader.in_comment = None, None, False
    loader.defined_functions, loader.dynamic_macros = {}, []

    class ProgramIterator:
        def __init__(self, items): self.items = items
        def __iter__(self): return self
        def __next__(self):
            if not self.items: raise StopIteration
            return self.items.pop(0)

    remaining_lines = [(ln, pt) for ln, ml in handlers.merge_lines(program_lines) for pt in handlers.split_lines(ml)]
    program_iter = ProgramIterator(remaining_lines)
    final_lines = []

    for line_num, raw_line in program_iter:
        loader.current_line_num = line_num
        line_strip = utils.canonicalize(utils.del_inline_comment(raw_line)).strip()
        if not line_strip: continue

        if line_strip.startswith("def") and "=>" in line_strip:
            pat, rest = raw_line.split('=>', 1)
            handlers.add_macro(pat[4:].strip() if pat.strip().startswith("def ") else pat.strip()[3:].strip(), rest.strip(), program_iter)
            continue

        if handlers.run_macro(line_strip, line_num, remaining_lines): continue

        m_alias = re.match(r'^(.+?)\s+as\s+([a-zA-Z_]\w*)$', line_strip)
        if m_alias and not line_strip.startswith(('"', "'")):
            handlers.register_alias(m_alias.group(2), m_alias.group(1).strip())
            continue

        raw_line = handlers.run_alias(raw_line)
        line = utils.canonicalize(utils.del_inline_comment(raw_line))
        if line.strip().startswith(('@set.', '@section.')):
            loader.current_section_name = (line.rsplit(' as ', 1)[0] if ' as ' in line else line).split()[0].split('.')[1]
            continue

        if line.strip().startswith("@python"):
            final_lines.append({"exec": "@python", "raw": raw_line, "num": line_num, "ctx": ""})
            continue

        if line.strip().startswith("func "):
            handlers.handle_function_definition(line, program_iter)
            continue

        if handlers.run_func(line.strip(), raw_line, line_num, final_lines): continue
        final_lines.append({"exec": line, "raw": raw_line, "num": line_num, "ctx": ""})

    lines_iter = iter(final_lines)
    for item in lines_iter:
        l, raw, ln, ctx = (item["exec"], item["raw"], item["num"], item.get("ctx", "")) if isinstance(item, dict) else (item, item, "?", "")
        line_to_process = (utils.canonicalize(utils.del_inline_comment(handlers.run_alias(l)))).strip()
        if not line_to_process: continue
        if not line_to_process.startswith('"'): line_to_process = line_to_process.lower()

        note_log, orig_note = '', utils.note
        def local_note(st): nonlocal note_log; note_log += st
        utils.note = local_note

        loader.current_exec_info = {"line": line_to_process, "raw": raw, "num": ln, "ctx": ctx}
        try:
            handlers.process_line(line_to_process, lines_iter)
        except Exception as e:
            utils.note = orig_note
            utils.report_error(e, getattr(args, 'input_file', None), getattr(loader, 'current_exec_info', None))

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
            else: raise utils.CompilerError(f'Label not found: {target}')
        loader.address_requests.clear()

        configure_memory_layout(overflow_initial_sp, resolved_adr, home_deps)
    except Exception as e:
        utils.report_error(e, getattr(args, 'input_file', None), getattr(loader, 'current_exec_info', None))

    if getattr(loader, 'is_pass1', False) or (loader.home == loader.home + len(loader.result) and loader.current_section_name is None): return None, None
    
    sys.stderr.write(utils.get_notes())
    print(f"=== {loader.home:#06x} -> {loader.home + len(loader.result):#06x}{f' ({loader.backup_address:#06x} -> {loader.backup_address + len(loader.result):#06x})' if loader.backup_address is not None else ''} ===")
    print(' '.join(f'{b:02x}' for b in loader.result))
    print('======')
    return loader.home, loader.result

def process_program(args, program_lines, overflow_initial_sp):
    loader.global_labels, loader.section_addresses, loader.label_sections, loader.aliases, loader.aliases_pattern = {}, {}, {}, {}, None

    sections = handlers.parse_sections(program_lines)
    
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
