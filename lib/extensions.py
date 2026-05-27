import os
import re
from .utils import note, to_lowercase, canonicalize, del_inline_comment

def load_extensions(path):
    if not os.path.exists(path):
        print(f"[WARN] No extension file found: {path}")
        return []

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    pattern = r"---syntax---\s*(.*?)\s*---logic---\s*(.*?)\s*---output---\s*(.*?)\s*(?=---syntax---|$)"
    matches = re.findall(pattern, content, re.DOTALL)

    extensions = []
    for syntax_block, logic_block, output_block in matches:
        extensions.append({
            "syntax": syntax_block.strip(),
            "logic": logic_block.strip(),
            "output": [ln.strip() for ln in output_block.strip().splitlines() if ln.strip()]
        })
    return extensions

def match_extension(line, extensions):
    for ext in extensions:
        syntax = ext["syntax"]
        pattern = re.escape(syntax)
        pattern = re.sub(r'\\\{(\w+)\\\}', r'(?P<\1>.+?)', pattern)
        
        m = re.fullmatch(pattern, line.strip())
        if m:
            return ext, m.groupdict()
    return None, None

def expand_extensions_in_program(program_lines, extensions):
    expanded = []
    for line in program_lines:
        line = line.split('---')[0].strip()
        if not line: continue
        
        current_line = line
        matched_full = False
        
        for ext in sorted(extensions, key=lambda x: len(x["syntax"]), reverse=True):
            pattern_str = re.escape(ext["syntax"]).replace(r"\{", "(?P<").replace(r"\}", ">.+?)")
            
            match = re.fullmatch(pattern_str, current_line)
            is_inline = False
            
            if not match:
                match = re.search(pattern_str, current_line)
                is_inline = True
            
            if match:
                local_env = match.groupdict()
                
                output_lines = []
                for out in ext["output"]:
                    temp = out
                    for k, v in local_env.items():
                        temp = temp.replace(f"{{{k}}}", str(v))
                    output_lines.append(temp)
                
                if is_inline and len(output_lines) == 1:
                    current_line = current_line[:match.start()] + output_lines[0] + current_line[match.end():]
                else:
                    expanded.extend(output_lines)
                    matched_full = True
                    break
        
        if not matched_full:
            expanded.append(current_line)
    return expanded