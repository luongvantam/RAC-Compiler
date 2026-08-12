import sys
import os
import re

def to_hex(val):
    if val.startswith('0x') or val.startswith('-0x'):
        return val
    try:
        return hex(int(val))
    except ValueError:
        return val

def load_syntax(filepath):
    if not os.path.exists(filepath):
        return []
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    rules = []
    blocks = content.split('===')
    for block in blocks:
        block = block.strip()
        if not block: continue
        
        syntax = ""
        output_template = []
        data_template = []
        
        mode = None
        for line in block.split('\n'):
            line = line.strip()
            if line == '---syntax---':
                mode = 'syntax'
            elif line == '---output---':
                mode = 'output'
            elif line == '---data---':
                mode = 'data'
            else:
                if mode == 'syntax':
                    syntax = line
                elif mode == 'output':
                    output_template.append(line)
                elif mode == 'data':
                    data_template.append(line)
        
        if not syntax:
            continue
            
        tokens = syntax.split()
        r_parts = []
        v_names = []
        for i, token in enumerate(tokens):
            if token.startswith('{') and token.endswith('}'):
                v_names.append(token[1:-1])
                if i == len(tokens) - 1:
                    r_parts.append(r'(.*)')
                else:
                    r_parts.append(r'([^,\s]+)')
            else:
                r_parts.append(re.escape(token))
        
        pattern = '^' + r'[,\s]+'.join(r_parts) + '$'
        
        rules.append({
            'regex': re.compile(pattern, re.IGNORECASE),
            'var_names': v_names,
            'output': output_template,
            'data': data_template
        })
    return rules

def render_template(lines, variables, sys_id):
    result = []
    for line in lines:
        rendered_line = line
        rendered_line = rendered_line.replace('{id}', str(sys_id))
        
        for var_name, var_val in variables.items():
            def mod_replace(match):
                mod = match.group(1)
                val = var_val
                if not mod:
                    return str(val)
                if mod == 'hex':
                    return str(to_hex(val))
                elif mod == 'safe':
                    s_val = str(val)[1:-1] if str(val).startswith('"') and str(val).endswith('"') else str(val)
                    safe = "".join(c if c.isalnum() else "_" for c in s_val)
                    return safe if safe else "str"
                elif mod == 'lower':
                    return str(val).lower()
                elif mod == 'raw':
                    if str(val).startswith('"') and str(val).endswith('"'):
                        return str(val)[1:-1]
                    return str(val)
                return str(val)
            
            pattern = r'\{' + re.escape(var_name) + r'(?::([a-z]+))?\}'
            rendered_line = re.sub(pattern, mod_replace, rendered_line)
            
        result.append(rendered_line)
    return result

def process_file(input_path, output_path, syntax_rules):
    with open(input_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    programs = []
    current_prog = None
    collecting_data = False
    print_id_counter = 1

    for raw_line in lines:
        line = raw_line.strip()
        
        if line.startswith('@PROGRAM '):
            name = line[len('@PROGRAM '):].strip()
            current_prog = {
                'name': name,
                'org': '0xd730',
                'backup': '0xe9e0',
                'main_code': [],
                'data': [],
                'vars': {},
                'in_dt_block': False
            }
            programs.append(current_prog)
            collecting_data = False
            print_id_counter = 1
        
        elif current_prog is not None:
            if current_prog.get('in_dt_block'):
                if line == ']':
                    current_prog['in_dt_block'] = False
                else:
                    if collecting_data:
                        current_prog['data'].append(raw_line.rstrip())
                    else:
                        current_prog['main_code'].append(raw_line.rstrip())
                continue

            if '->' in line and not line.startswith('lbl '):
                val, var_name = line.split('->', 1)
                current_prog['vars'][var_name.strip()] = val.strip()
                continue
                
            if line.startswith('ORG '):
                current_prog['org'] = line[len('ORG '):].strip()
            elif line.startswith('BACKUP '):
                current_prog['backup'] = line[len('BACKUP '):].strip()
            elif line.startswith('@DATA '):
                collecting_data = True
            elif line.startswith('DT '):
                match = re.match(r'DT\s+([A-Z0-9_]+)\s+(.*)', line)
                if match:
                    dt_name, dt_data = match.groups()
                    if collecting_data:
                        current_prog['data'].append(f"lbl {dt_name}")
                    else:
                        current_prog['main_code'].append(f"lbl {dt_name}")
                    
                    if dt_data.strip() == '[':
                        current_prog['in_dt_block'] = True
                    else:
                        if collecting_data:
                            current_prog['data'].append(dt_data)
                        else:
                            current_prog['main_code'].append(dt_data)
            else:
                # Try matching dynamic rules
                matched_rule = False
                for rule in syntax_rules:
                    match = rule['regex'].match(line)
                    if match:
                        matched_rule = True
                        
                        # Build local variables mapping
                        local_vars = {}
                        for i, var_name in enumerate(rule['var_names']):
                            val = match.group(i + 1)
                            # resolve virtual vars
                            val = current_prog['vars'].get(val, val)
                            local_vars[var_name] = val
                        
                        rendered_out = render_template(rule['output'], local_vars, print_id_counter)
                        rendered_data = render_template(rule['data'], local_vars, print_id_counter)
                        
                        current_prog['main_code'].extend(rendered_out)
                        current_prog['data'].extend(rendered_data)
                        
                        print_id_counter += 1
                        break
                
                if not matched_rule:
                    if collecting_data:
                        if line: 
                            current_prog['data'].append(raw_line.rstrip())
                    else:
                        if line or current_prog['main_code']: 
                            current_prog['main_code'].append(raw_line.rstrip())

    # Write output
    with open(output_path, 'w', encoding='utf-8') as f:
        for prog in programs:
            name = prog['name']
            org_part = f" at {prog['org']}" if prog['org'] else ""
            backup_part = f" backup {prog['backup']}" if prog['backup'] else ""
            
            f.write(f"@section.{name}{org_part}{backup_part}\n")
            
            # Remove trailing empty lines from main_code
            while prog['main_code'] and not prog['main_code'][-1].strip():
                prog['main_code'].pop()
                
            for code_line in prog['main_code']:
                # Do not re-add org and backup if they were accidentally collected
                if code_line.strip() not in (f"ORG {prog['org']}", f"BACKUP {prog['backup']}"):
                    f.write(code_line + "\n")
            
            # Ensure brk before data
            has_brk = False
            if prog['main_code'] and prog['main_code'][-1].strip() == 'brk':
                has_brk = True
                
            if not has_brk:
                f.write("brk\n")

            # Print data
            if prog['data']:
                for data_line in prog['data']:
                    f.write(data_line + "\n")
            
            f.write("\n")

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python interpreter_580vnx.py <input_file> <output_file>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    syntax_file = os.path.join(script_dir, 'syntax.txt')
    syntax_rules = load_syntax(syntax_file)
    
    if not os.path.exists(input_file):
        print(f"Error: Input file {input_file} not found.")
        sys.exit(1)
        
    process_file(input_file, output_file, syntax_rules)
    print(f"Processed {input_file} -> {output_file}")
