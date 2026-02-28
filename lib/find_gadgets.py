import re

def normalize_instruction(instr: str) -> str:
    instr = instr.lower()
    instr = re.sub(r"\s+", "", instr)
    return instr

def expand_register_pattern(text, defined_vars):
    def repl(match):
        name = match.group(1)
        constraint_pattern = r"(?:[0-9]|1[0-5])"
        if "[" in name:
            m = re.match(r"(\w+)\[(\d+)\]", name)
            if not m:
                raise ValueError("Invalid constraint syntax")
            var, constraint = m.groups()

            if constraint == "1":
                constraint_pattern = r"[0-9]"  # 0–9
            else:
                raise ValueError("Unsupported constraint")
        else:
            var = name
        if var in defined_vars:
            return rf"(?P={var})"
        defined_vars.add(var)
        return rf"(?P<{var}>{constraint_pattern})"
    return re.sub(r"\{([^}]+)\}", repl, text)

def build_full_regex(instructions):
    line_prefix = r'^\s*'
    line_suffix = r'\s*;\s*[0-9a-fA-F]+\s*\|\s*[0-9a-fA-F]+'
    pattern = ""
    defined_vars = set()
    for i, instr in enumerate(instructions):
        instr = normalize_instruction(instr)
        instr = expand_register_pattern(instr, defined_vars)
        pattern += line_prefix + instr + line_suffix
        if i != len(instructions) - 1:
            pattern += r'\r?\n'
    return pattern

def normalize_disassembly(content):
    lines = content.splitlines()
    normalized_lines = []
    for line in lines:
        parts = line.split(";")
        if len(parts) >= 2:
            instr = normalize_instruction(parts[0])
            comment = ";" + parts[1]
            normalized_lines.append(instr + comment)
        else:
            normalized_lines.append(line)
    return "\n".join(normalized_lines)

def find_first_gadget(instructions, disas_file):
    pattern = build_full_regex(instructions)
    with open(disas_file, "r", encoding="utf-8", errors="ignore") as f:
        raw_content = f.read()
    content = normalize_disassembly(raw_content)
    match = re.search(pattern, content, re.MULTILINE)
    if not match:
        return None
    block = match.group(0)
    first_line = block.splitlines()[0]
    addr_match = re.search(r";\s*([0-9a-fA-F]+)", first_line)
    if not addr_match:
        return None
    address = addr_match.group(1)
    return f"0x{address}"
