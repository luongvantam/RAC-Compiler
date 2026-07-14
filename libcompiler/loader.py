from libcompiler.i18n import t
import re
from libcompiler.utils import note, canonicalize, del_inline_comment
from libcompiler import utils

commands, datalabels, labels, vars_dict, disasm, char_to_hex, token_to_hex = {}, {}, {}, {}, {}, {}, {}
disas_filename, home, current_section_name, in_comment = None, None, None, False
result, address_requests, relocation_expressions, sizeof_cmds, deferred_evals, pr_org_cmds, pr_backup_cmds = [], [], [], [], [], [], []

def add_command(command_dict, address, command, tags, debug_info=''):
    if not command or type(command_dict) is not dict:
        raise utils.CompilerError(t("err_empty_commanddict_var0_da33", var0=debug_info))
    if any(command.startswith(p) for p in ('0x', 'call', 'goto')):
        raise utils.CompilerError(t("err_command_starts_with_disallowed_5347", var0=debug_info))
    if command.endswith(':') or ';' in command:
        raise utils.CompilerError(t("err_invalid_command_syntax_var0_34ec", var0=debug_info))
    if command in command_dict:
        if command_dict[command] == (address, tuple(tags)):
            return
        raise utils.CompilerError(t("err_command_var0_appears_twice_6c42", var0=command, var1=debug_info))
    command_dict[command] = (address, tuple(tags))

def get_commands(gadgets_file, labels_file):
    global commands, datalabels
    with open(gadgets_file, 'r', encoding='utf-8') as f:
        raw = re.sub(r'/\*.*?\*/', '', f.read(), flags=re.DOTALL)
        for i, line in enumerate(raw.splitlines()):
            line = del_inline_comment(line).strip()
            if not line:
                continue
            m = re.fullmatch(r'([0-9a-fA-F]+)\s+(.+)', line)
            if m:
                addr, cmd_raw = int(m.group(1), 16), canonicalize(m.group(2)).lower()
                tags = []
                while cmd_raw.startswith('{'):
                    end = cmd_raw.find('}')
                    tags.append(cmd_raw[1:end])
                    cmd_raw = cmd_raw[end+1:].strip()
                for sub in [c.strip() for c in cmd_raw.split(';') if c.strip()]:
                    add_command(commands, addr, canonicalize(sub).lower(), tags, f'at {gadgets_file}:{i+1}')
    
    with open(labels_file, 'r', encoding='u8') as f:
        last_global = None
        for i, line in enumerate(f.read().splitlines()):
            m = re.match(r'^\s*([\w_.]+)\s+(.+)', line)
            if not m:
                continue
            raw = m.group(1)
            reals = [r.strip() for r in del_inline_comment(m.group(2)).split(';') if r.strip() and not r.strip().startswith('.')]
            if not reals:
                continue
            
            d_match = re.fullmatch(r'd_([0-9a-fA-F]+)', raw)
            if d_match:
                for r in reals:
                    datalabels[r] = int(d_match.group(1), 16)
                continue
                
            addr = None
            if re.fullmatch(r'[0-9a-fA-F]+', raw):
                addr, last_global = int(raw, 16), None
            else:
                g_match = re.match(r'f_([0-9a-fA-F]+)', raw)
                if g_match:
                    addr = int(g_match.group(1), 16)
                    if len(g_match.group(0)) == len(raw):
                        last_global = addr
                    else:
                        l_match = re.fullmatch(r'\.l_([0-9a-fA-F]+)', raw[len(g_match.group(0)):])
                        if l_match:
                            addr += int(l_match.group(1), 16)
                else:
                    l_match = re.fullmatch(r'\.l_([0-9a-fA-F]+)', raw)
                    if l_match and last_global is not None:
                        addr = last_global + int(l_match.group(1), 16)
            
            if addr is not None:
                if disasm.get(addr, '').startswith('push lr'):
                    tags = ('del lr',)
                    addr += 2
                else:
                    tags = ('rt',)
                    a1 = addr + 2
                    while a1 <= 0x3ffff and not any(disasm.get(a1, '').startswith(x) for x in ('push lr', 'pop pc', 'rt')):
                        a1 += 2
                    if not disasm.get(a1, '').startswith('rt'):
                        tags += ('del lr',)
                
                for r in reals:
                    if r not in commands or 'override rename list' not in commands[r][1]:
                        if r in commands and commands[r] == (addr, tags):
                            note(f'Warning: Duplicated command {r}\n')
                            continue
                        add_command(commands, addr, r, tags, f'at {labels_file}:{i+1}')

def get_disassembly(filename):
    global disasm
    with open(filename, 'r', encoding='u8') as f:
        disasm = {int(p[1].split('|', 1)[0].strip(), 16): p[0].strip() 
                  for line in f if line.startswith('\t') and ';' in line 
                  for p in [line.split(';', 1)] if '|' in p[1]}

def sizeof_register(reg_name):
    return {
        'r': 2, 
        'e': 2, 
        'x': 4, 
        'q': 8,
        'l': 4
    }[reg_name[0]]