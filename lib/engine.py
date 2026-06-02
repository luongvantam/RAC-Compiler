import re
import os
import sys
from .utils import to_lowercase, canonicalize, del_inline_comment
from . import utils
from . import loader
from .optimizer import byte_to_key, get_npress, get_npress_adr
from .handlers import dispatch_command_handler, handle_function_definition

def process_line(line, program_iter=None):
    line = line.split('---')[0].strip()

    if not line or line.isspace():
        return

    if line.startswith('/*'):
        loader.in_comment = True
        return
        
    if '*/' in line:
        loader.in_comment = False
        return
        
    if loader.in_comment:
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
    for pos, left_offset, left_label, right_offset, right_label, op in loader.relocation_expressions:
        if left_label not in loader.labels or right_label not in loader.labels:
            if getattr(loader, 'is_pass1', False):
                continue
            raise ValueError(f'Label not found in adr: {left_label}, {right_label}')
        left_addr = loader.labels[left_label] + left_offset
        right_addr = loader.labels[right_label] + right_offset
        
        if op == '+':
            result_addr = (left_addr + right_addr) & 0xFFFF
        else:
            result_addr = (left_addr - right_addr) & 0xFFFF
        
        if not getattr(loader, 'is_pass1', False):
            if loader.result[pos] != 0 or loader.result[pos+1] != 0:
                print(f"[WARN] adr overwrite at {pos:04X}")
        loader.result[pos] = result_addr & 0xFF
        loader.result[pos + 1] = (result_addr >> 8) & 0xFF

    for pos in loader.pr_length_cmds:
        pr_length = len(loader.result)
        if not getattr(loader, 'is_pass1', False):
            if loader.result[pos] != 0 or loader.result[pos+1] != 0:
                print(f"[WARN] pr_length overwrite at {pos:04X}")
        loader.result[pos] = pr_length & 0xFF
        loader.result[pos + 1] = (pr_length >> 8) & 0xFF

    loader.relocation_expressions.clear()
    loader.pr_length_cmds.clear()


def _split_into_sections(program_lines):
    """Return list of (name, lines) tuples by splitting on @set.<name> directives.
    Lines before the first @set are grouped under name None.  The directive
    itself is not included in the section contents.
    
    Supports:
    - @section.<name> at <addr_org>
    - @section.<name> at <addr_org> backup <addr_backup>
    """
    sections = []
    current_name = None
    current_lines = []
    for raw_line in program_lines:
        stripped = raw_line.strip()
        if stripped.startswith('@set.') or stripped.startswith('@section.'):
            parts = stripped.split("at", 1)
            name_part = parts[0].strip()
            if current_name is not None or current_lines:
                sections.append((current_name, current_lines))
            current_name = name_part[5:] if name_part.startswith('@set.') else name_part[9:]
            current_lines = []
            if len(parts) > 1:
                addr_part = parts[1].strip()
                if "backup" in addr_part:
                    addr_subparts = addr_part.split("backup", 1)
                    org_addr = addr_subparts[0].strip()
                    backup_addr = addr_subparts[1].strip()
                    
                    if org_addr:
                        current_lines.append("org " + org_addr)
                    if backup_addr:
                        current_lines.append("backup " + backup_addr)
                else:
                    current_lines.append("org " + addr_part)
        else:
            current_lines.append(raw_line)
    if current_name is not None or current_lines:
        sections.append((current_name, current_lines))
    return sections


def process_program(args, program_lines, overflow_initial_sp):
    loader.global_labels = {}
    loader.section_addresses = {}
    # split into sections and dispatch to helper for each
    sections = _split_into_sections(program_lines)
    # reorder so named sections come before unnamed to avoid warning prints
    named = [(n, l) for n, l in sections if n is not None]
    unnamed = [(n, l) for n, l in sections if n is None]
    sections = named + unnamed

    if len(sections) == 1:
        # simple case, just process the single list of lines
        loader.is_pass1 = False
        loader.current_section_name = sections[0][0]
        return _process_program_core(args, sections[0][1], overflow_initial_sp)

    # multiple sections: process each independently
    # Pass 1: Collect globals and section addresses silently
    loader.is_pass1 = True
    for name, lines in sections:
        loader.current_section_name = name
        _process_program_core(args, lines, overflow_initial_sp)
        
    # Pass 2: Actually resolve cross-section dependencies and print
    loader.is_pass1 = False
    for name, lines in sections:
        loader.current_section_name = name
        if name is not None:
            print(f"\n=== section @{name} ===")
        _process_program_core(args, lines, overflow_initial_sp)
    loader.current_section_name = None


def _process_program_core(args, program_lines, overflow_initial_sp):
    if not hasattr(loader, 'global_labels'):
        loader.global_labels = {}
    if not hasattr(loader, 'section_addresses'):
        loader.section_addresses = {}
    loader.result = []
    loader.labels = {}
    loader.address_requests = []
    loader.relocation_expressions = []
    loader.pr_length_cmds = []
    loader.deferred_evals = []
    loader.home = None
    loader.in_comment = False
    loader.backup_address = None
    loader.dist_cmds = []
    
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

        m = re.match(r'(\w+)\s*\(((?:[^()]+|\([^()]*\))*)\)', line.strip())
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
                        "exec": f"var {param_def.strip()} = {arg_val}",
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
            original_note_func = utils.note

            def local_note_func(st):
                nonlocal note_log
                note_log += st
            
            utils.note = local_note_func
            old_len_result = len(loader.result)
            
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
                print(f"    {'^' * len(raw_origin.strip())}")
                print(f"CompilerError: {str(e)}")
                sys.exit()

            if args.format == 'key' and \
                    any(x != 0 and get_npress(x) > 100 for x in loader.result[old_len_result:]):
                local_note_func('Line generates many keypresses\n')

            utils.note = original_note_func
            if note_log and not getattr(loader, 'is_pass1', False):
                utils.note(note_log)

    eval_scope = {}
    for k, v in loader.vars_dict.items():
        if isinstance(v, list):
             eval_scope[k] = int.from_bytes(bytes(v), 'little')
        else:
             eval_scope[k] = v

    for label_name in loader.labels.keys():
         if label_name not in eval_scope:
            eval_scope[label_name] = label_name

    def adr_eval(label, offset=0):
        if not isinstance(label, str):
             raise ValueError(f"Label in adr() must be a string, but got {label} (type {type(label)})")
        if label not in loader.labels:
            if hasattr(loader, 'global_labels') and label in loader.global_labels:
                return loader.global_labels[label] + offset
            if getattr(loader, 'is_pass1', False):
                return 0
            raise ValueError(f'Label not found during deferred eval: {label}')
        return (loader.labels[label] + offset)

    eval_scope['adr'] = adr_eval
    home_dependent_evals = [] 
    temp_deferred_evals = list(loader.deferred_evals)
    loader.deferred_evals.clear() 
    
    for pos, expr in temp_deferred_evals:
        try:
            val = utils.safe_eval(expr, eval_scope)
        except Exception as e:
            try:
                temp_scope = eval_scope.copy()
                for k, v in temp_scope.items():
                    if isinstance(v, str) and v.startswith("eval("):
                         temp_scope[k] = utils.safe_eval(v[5:-1], temp_scope)
                val = utils.safe_eval(expr, temp_scope)
            except Exception as e2:
                 raise ValueError(f"Deferred eval error in expression {expr!r}: {e2}")
        
        if not isinstance(val, int):
            raise ValueError(f"Deferred eval {expr!r} did not return an integer")
        
        referenced_labels = re.findall(r'adr\(\s*["\']?([a-zA-Z_0-9]+)', expr)
        is_absolute_address = (expr.count('adr(') > 1) or any(
            (label in loader.global_labels and label not in loader.labels)
            for label in referenced_labels
        )
        
        if is_absolute_address:
            val = val & 0xFFFF
            if not getattr(loader, 'is_pass1', False):
                if loader.result[pos] != 0 or loader.result[pos+1] != 0:
                    print(f"[WARN] eval_abs overwrite at {pos:04X}")
            loader.result[pos] = val & 0xFF
            loader.result[pos + 1] = (val >> 8) & 0xFF
        else:
            home_dependent_evals.append((pos, val))
            
    finalize_processing()
    
    resolved_adr_cmds = []
    for source_adr, offset, target_label in loader.address_requests:
        if target_label in loader.labels:
            resolved_adr_cmds.append((source_adr, loader.labels[target_label] + offset))
        elif target_label in loader.global_labels:
            resolved_adr_cmds.append((source_adr, loader.global_labels[target_label] - loader.home + offset))
        else:
            if getattr(loader, 'is_pass1', False):
                resolved_adr_cmds.append((source_adr, 0))
                continue
            raise ValueError(f'Label not found: {target_label} (for adr() at pos {source_adr})')
    
    loader.address_requests.clear()
    
    if args.target in ('none', 'overflow'):
        if args.target == 'overflow':
            assert len(loader.result) <= 100, 'Program too long'

        if loader.home is None:
            loader.home = overflow_initial_sp
            if 'home' in loader.labels:
                loader.home -= loader.labels['home']
                if loader.home + len(loader.result) > 0x8E00:
                    # suppress warning if section has a name (assuming named sections are handled first)
                    if loader.current_section_name is None and not getattr(loader, 'is_pass1', False):
                        utils.note(f'Warning: Program length after home = {len(loader.result)} bytes'
                            f' > {0x8E00 - loader.home} bytes\n')

            min_home = loader.home
            while min_home >= 0x8154 + 200:
                min_home -= 100
            while loader.home + len(loader.result) <= 0x8E00:
                loader.home += 100
            
            all_home_dependencies = resolved_adr_cmds + home_dependent_evals
            
            loader.home = min(range(min_home, loader.home, 100), key=lambda home_val:
                        (
                             sum(
                                 get_npress_adr(home_val + home_offset) >= 100
                                 for source_adr, home_offset in all_home_dependencies
                             ),
                             -home_val
                        )
                        )

    elif args.target == 'loader':
        if loader.home is None:
            loader.home = 0x85b0 - len(loader.result)
            entry = loader.home + loader.labels.get('home', 0) - 2
            loader.result.extend((0x6a, 0x4f, 0, 0, entry & 255, entry >> 8, 0x68, 0x4f, 0, 0))
            while loader.home + len(loader.result) < 0x85d7:
                loader.result.append(0)
            loader.result.extend((0xff, 0xae, 0x85))
            home2 = 0
            assert (loader.home - home2) >= 0x8501, 'Program too long'
            while get_npress_adr(loader.home - home2) >= 100:
                home2 += 1

    else:
        assert False, 'Internal error'

    assert loader.home is not None

    for source_adr, home_offset in resolved_adr_cmds:
        target_adr = loader.home + home_offset
        if not getattr(loader, 'is_pass1', False):
            if loader.result[source_adr] != 0 or loader.result[source_adr + 1] != 0:
                print(f"[WARN] adr overwrite at {source_adr:04X}, old={loader.result[source_adr]:02X}{loader.result[source_adr+1]:02X}")
        loader.result[source_adr] = target_adr & 0xFF
        loader.result[source_adr + 1] = target_adr >> 8

    for source_adr, home_offset in home_dependent_evals:
        target_adr = loader.home + home_offset
        if not getattr(loader, 'is_pass1', False):
            if loader.result[source_adr] != 0 or loader.result[source_adr + 1] != 0:
                print(f"[WARN] eval_adr overwrite at {source_adr:04X}, old={loader.result[source_adr]:02X}{loader.result[source_adr+1]:02X}")
        loader.result[source_adr] = target_adr & 0xFF
        loader.result[source_adr + 1] = target_adr >> 8

    for label, home_offset in loader.labels.items():
        loader.global_labels[label] = loader.home + home_offset
        if not getattr(loader, 'is_pass1', False):
            utils.note(f'Label {label} is at address {loader.home + home_offset:04X}\n')

    if loader.current_section_name is not None:
        loader.section_addresses[loader.current_section_name] = {
            'org': loader.home,
            'backup': loader.backup_address
        }

    # Resolve dist.<section> commands
    for pos, target_section in loader.dist_cmds:
        if target_section not in loader.section_addresses:
            if getattr(loader, 'is_pass1', False):
                continue
            raise ValueError(f"Section '{target_section}' not found or not yet processed for dist calculation")
        sec_meta = loader.section_addresses[target_section]
        if sec_meta['backup'] is None:
            if getattr(loader, 'is_pass1', False):
                continue
            raise ValueError(f"Section '{target_section}' has no backup address defined")
        dist_val = (sec_meta['backup'] - sec_meta['org']) & 0xFFFF
        if not getattr(loader, 'is_pass1', False):
            if loader.result[pos] != 0 or loader.result[pos+1] != 0:
                print(f"[WARN] dist overwrite at {pos:04X}")
        loader.result[pos] = dist_val & 0xFF
        loader.result[pos+1] = (dist_val >> 8) & 0xFF
            
    if args.target == 'overflow':
        hackstring = list(map(ord, '1234567890' * 10))
        for home_offset, byte in enumerate(loader.result):
            assert isinstance(byte, int), (home_offset, byte)
            hackstring_pos = (loader.home + home_offset - 0x8154) % 100
            hackstring[hackstring_pos] = byte

    # Stop here if we're only in Pass 1
    if getattr(loader, 'is_pass1', False):
        return

    # wrap output with section header/footer if needed
    header_printed = False
    def _print_header():
        nonlocal header_printed
        if header_printed:
            return
        header_printed = True
        if loader.backup_address is None:
            print(f"=== {loader.home:#06x} -> {loader.home + len(loader.result):#06x} ===")
        else:
            print(f"=== {loader.home:#06x} -> {loader.home + len(loader.result):#06x} (backup : {loader.backup_address:#06x} -> {loader.backup_address + len(loader.result):#06x}) ===")
    def _print_footer():
        print('=====')
        
    if loader.home == loader.home+len(loader.result) and loader.current_section_name is None:
        return

    _print_header()

    if args.target == 'overflow' and args.format == 'hex':
        print(''.join(f'{byte:02x}' for byte in hackstring))

    elif args.target == 'none' and args.format == 'hex':
        print(f'{loader.home:#06x}:', ' '.join(f'{b:02x}' for b in loader.result))

    elif args.target == 'none' and args.format == 'key':
        print(f'{loader.home:#06x}:', ' '.join(byte_to_key(b) for b in loader.result))

    elif args.target == 'loader' and args.format == 'key':
        addr = loader.home - home2
        print('Address to load:',
            byte_to_key(addr & 0xff),
            byte_to_key((addr >> 8) & 0xff))

        loader.result = [0] * home2 + loader.result

        print(" ".join(f"{x:02X}" for x in loader.result))

    elif args.target == 'overflow' and args.format == 'key':
        print(' '.join(byte_to_key(x) for x in hackstring))

    else:
        raise ValueError('Unsupported target/format combination')

    _print_footer()