import re
from utils import note, canonicalize, del_inline_comment

max_call_adr = 0x3ffff
commands, datalabels, labels, vars_dict, disasm = {}, {}, {}, {}, {}
disas_filename, home, current_section_name, in_comment = None, None, None, False
result, address_requests, relocation_expressions, sizeof_cmds, deferred_evals = [], [], [], [], []

def add_command(command_dict, address, command, tags, debug_info=''):
    assert command and type(command_dict) is dict, f'Empty command/dict {debug_info}'
    assert not any(command.startswith(p) for p in ('0x', 'call', 'goto')), f'Command starts with disallowed {debug_info}'
    assert not command.endswith(':') and ';' not in command, f'Invalid command syntax {debug_info}'
    if command in command_dict:
        if command_dict[command] == (address, tuple(tags)): return
        assert False, f'Command {command} appears twice {debug_info}'
    command_dict[command] = (address, tuple(tags))

def get_commands(gadgets_file, labels_file):
    global commands, datalabels
    with open(gadgets_file, 'r', encoding='utf-8') as f:
        raw = re.sub(r'/\*.*?\*/', '', f.read(), flags=re.DOTALL)
        for i, line in enumerate(raw.splitlines()):
            line = del_inline_comment(line).strip()
            if not line: continue
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
            if not m: continue
            raw, reals = m.group(1), [r.strip() for r in del_inline_comment(m.group(2)).split(';') if r.strip() and not r.strip().startswith('.')]
            if not reals: continue
            
            d_match = re.fullmatch(r'd_([0-9a-fA-F]+)', raw)
            if d_match:
                for r in reals: datalabels[r] = int(d_match.group(1), 16)
                continue
                
            addr = None
            if re.fullmatch(r'[0-9a-fA-F]+', raw): 
                addr, last_global = int(raw, 16), None
            else:
                g_match = re.match(r'f_([0-9a-fA-F]+)', raw)
                if g_match:
                    addr = int(g_match.group(1), 16)
                    if len(g_match.group(0)) == len(raw): last_global = addr
                    else:
                        l_match = re.fullmatch(r'\.l_([0-9a-fA-F]+)', raw[len(g_match.group(0)):])
                        if l_match: addr += int(l_match.group(1), 16)
                else:
                    l_match = re.fullmatch(r'\.l_([0-9a-fA-F]+)', raw)
                    if l_match and last_global is not None: addr = last_global + int(l_match.group(1), 16)
            
            if addr is not None:
                tags = ('del lr',) if disasm.get(addr, '').startswith('push lr') else ('rt',)
                if tags[0] != 'del lr':
                    a1 = addr + 2
                    while a1 <= 0x3ffff and not any(disasm.get(a1, '').startswith(x) for x in ('push lr', 'pop pc', 'rt')): a1 += 2
                    if not disasm.get(a1, '').startswith('rt'): tags += ('del lr',)
                
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
    return {'r': 1, 'e': 2, 'x': 4, 'q': 8}[reg_name[0]]

# only fx580vnx
char_to_hex = {
    "0": "30",
    "1": "31",
    "2": "32",
    "3": "33",
    "4": "34",
    "5": "35",
    "6": "36",
    "7": "37",
    "8": "38",
    "9": "39",
    "A": "41",
    "B": "42",
    "C": "43",
    "D": "44",
    "E": "45",
    "F": "46",
    "G": "47",
    "H": "48",
    "I": "49",
    "J": "4A",
    "K": "4B",
    "L": "4C",
    "M": "4D",
    "N": "4E",
    "O": "4F",
    "P": "50",
    "Q": "51",
    "R": "52",
    "S": "53",
    "T": "54",
    "U": "55",
    "V": "56",
    "W": "57",
    "X": "58",
    "Y": "59",
    "Z": "5A",
    "a": "61",
    "b": "62",
    "c": "63",
    "d": "64",
    "e": "65",
    "f": "66",
    "g": "67",
    "h": "68",
    "i": "69",
    "j": "6A",
    "k": "6B",
    "l": "6C",
    "m": "6D",
    "n": "6E",
    "o": "6F",
    "p": "70",
    "q": "71",
    "r": "72",
    "s": "73",
    "t": "74",
    "u": "75",
    "v": "76",
    "w": "77",
    "x": "78",
    "y": "79",
    "z": "7A",
    "Á": "F451",
    "á": "F471",
    "À": "F450",
    "à": "F470",
    "Ả": "F454",
    "ả": "F474",
    "Ã": "F453",
    "ã": "F473",
    "Ạ": "F410",
    "ạ": "F465",
    "Ă": "F455",
    "ă": "F475",
    "Ắ": "F411",
    "ắ": "F431",
    "Ằ": "F412",
    "ằ": "F432",
    "Ẳ": "F490",
    "ẳ": "F456",
    "Ẵ": "F491",
    "ẵ": "F457",
    "Ặ": "F413",
    "ặ": "F433",
    "Â": "F452",
    "â": "F472",
    "Ấ": "F414",
    "ấ": "F434",
    "Ầ": "F415",
    "ầ": "F435",
    "Ẩ": "F416",
    "ẩ": "F436",
    "Ẫ": "F492",
    "ẫ": "F477",
    "Ậ": "F417",
    "ậ": "F437",
    "É": "F459",
    "é": "F479",
    "È": "F458",
    "è": "F478",
    "Ẻ": "F45B",
    "ẻ": "F47B",
    "Ẽ": "F418",
    "ẽ": "F438",
    "Ẹ": "F419",
    "ẹ": "F439",
    "Ê": "F45A",
    "ê": "F47A",
    "Ế": "F41A",
    "ế": "F43A",
    "Ề": "F41B",
    "ề": "F43B",
    "Ể": "F41C",
    "ể": "F43C",
    "Ễ": "F41D",
    "ễ": "F43D",
    "Ệ": "F41E",
    "ệ": "F43E",
    "Í": "F45D",
    "í": "F47D",
    "Ì": "F45C",
    "ì": "F47C",
    "Ỉ": "F42B",
    "ỉ": "F47F",
    "Ĩ": "F45E",
    "ĩ": "F47E",
    "Ị": "F428",
    "ị": "F448",
    "Ó": "F463",
    "ó": "F483",
    "Ò": "F462",
    "ò": "F482",
    "Ỏ": "F429",
    "ỏ": "F486",
    "Õ": "F430",
    "õ": "F485",
    "Ọ": "F42A",
    "ọ": "F487",
    "Ô": "F464",
    "ô": "F484",
    "Ố": "F41F",
    "ố": "F43F",
    "Ồ": "F420",
    "ồ": "F440",
    "Ổ": "F421",
    "ổ": "F441",
    "Ỗ": "F422",
    "ỗ": "F442",
    "Ộ": "F423",
    "ộ": "F445",
    "Ơ": "F444",
    "ơ": "F44D",
    "Ớ": "F425",
    "ớ": "F44E",
    "Ờ": "F426",
    "ờ": "F446",
    "Ở": "F427",
    "ở": "F447",
    "Ỡ": "F443",
    "ỡ": "F46E",
    "Ợ": "F424",
    "ợ": "F48E",
    "Ú": "F46A",
    "ú": "F48A",
    "Ù": "F469",
    "ù": "F489",
    "Ủ": "F42C",
    "ủ": "F48C",
    "Ũ": "F42D",
    "ũ": "F48B",
    "Ụ": "F42E",
    "ụ": "F488",
    "Ư": "F44F",
    "ư": "F46F",
    "Ứ": "F44A",
    "ứ": "F461",
    "Ừ": "F44B",
    "ừ": "F467",
    "Ử": "F44C",
    "ử": "F468",
    "Ữ": "F48F",
    "ữ": "F476",
    "Ự": "F449",
    "ự": "F481",
    "Ý": "F46D",
    "ý": "F48D",
    "Ỳ": "F42F",
    "ỳ": "F45F",
    "Ỷ": "F493",
    "ỷ": "F466",
    "Ỹ": "F494",
    "ỹ": "F46B",
    "Ỵ": "F495",
    "ỵ": "F46C",
    "Đ": "F460",
    "đ": "F480",
    "~": "20",
    "@": "40",
    "_": "5F",
    "&": "1A",
    "-": "2D",
    "+": "2B",
    "(": "28",
    ")": "29",
    "/": "2F",
    "*": "2A",
    "'": "27",
    ":": "3A",
    "!": "21",
    "?": "3F",
    "|": "7C",
    "√": "98",
    "÷": "26",
    "×": "24",
    "^": "5E",
    "°": "85",
    "{": "7B",
    "}": "7D",
    "[": "5B",
    "]": "5D",
    "%": "25",
    ".": "2E",
    ",": "2C",
}

token_to_hex = {
    "_" : "00",
    "e" : "21",
    "pi" : "22",
    "𝜋" : "22",
    "," : "2c",
    "x10^" : "2d",
    "." : "2e",
    "0" : "30",
    "1" : "31",
    "2" : "32",
    "3" : "33",
    "4" : "34",
    "5" : "35",
    "6" : "36",
    "7" : "37",
    "8" : "38",
    "9" : "39",
    "m" : "40",
    "ans" : "41",
    "a" : "42",
    "b" : "43",
    "c" : "44",
    "d" : "45",
    "e" : "46",
    "f" : "47",
    "x" : "48",
    "y" : "49",
    "preans" : "4a",
    "z" : "4b",
    "∑(" : "50",
    "sigma(" : "50",
    "∫(" : "51",
    "integral(" : "51",
    "d/dx" : "52",
    "∏(" : "53",
    "capital_pi(" : "53",
    "(" : "60",
    "abs(" : "68",
    "rnd(" : "69",
    "sinh(" : "6C",
    "cosh(" : "6D",
    "tanh(" : "6E",
    "sinh^-1(" : "6F",
    "cosh^-1(" : "70",
    "tanh^-1(" : "71",
    "e^(" : "72",
    "10^(" : "73",
    "√(" : "74",
    "sqrt(" : "74",
    "ln(" : "75",
    "³√(" : "76",
    "cbrt(" : "76",
    "sin(" : "77",
    "cos(" : "78",
    "tan(" : "79",
    "sin^-1(" : "7a",
    "cos^-1(" : "7b",
    "tan^-1(" : "7c",
    "log(" : "7d",
    "int(" : "83",
    "intg(" : "84",
    "ranint#(" : "87",
    "gcd(" : "88",
    "lcm(" : "89",
    "rndfix(" : "8a",
    "=" : "a5",
    "+" : "a6",
    "-" : "a7",
    "*" : "a8",
    "÷" : "a9",
    "//" : "a9",
    "mod(" : "aa",
    "−" : "c0",
    "⌟" : "c8",
    "/" : "c8",
    "^(" : "c9",
    "x^√(" : "ca",
    "root(" : "ca",
    ")" : "d0",
    "^-1" : "d4",
    "^2" : "d5",
    "^3" : "d6",
    "%" : "d7",
    "!" : "d8"
}