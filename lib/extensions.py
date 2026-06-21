import os
import re

def load_extensions(path):
    if not os.path.exists(path):
        print(f"[WARN] No extension file found: {path}")
        return []

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    pattern = r"---syntax---\s*(.*?)\s*---output---\s*(.*?)\s*(?=---syntax---|$)"
    matches = re.findall(pattern, content, re.DOTALL)

    extensions = []
    for syntax_block, output_block in matches:
        syntax = syntax_block.strip()
        pattern_str = re.escape(syntax).replace(r"\{", "(?P<").replace(r"\}", ">.+?)")
        compiled = re.compile(pattern_str)
        extensions.append({
            "syntax": syntax,
            "output": [ln.strip() for ln in output_block.strip().splitlines() if ln.strip()],
            "compiled_pattern": compiled
        })
    # Pre-sort extensions by syntax length descending to avoid sorting during program expansion
    extensions.sort(key=lambda x: len(x["syntax"]), reverse=True)
    return extensions

def expand_extensions_in_program(program_lines, extensions):
    expanded = []
    for idx, line in enumerate(program_lines):
        line_num = idx + 1
        line = line.split('---')[0].strip()
        if not line: continue
        
        current_line = line
        matched_full = False
        
        for ext in extensions:
            compiled = ext["compiled_pattern"]
            match = compiled.fullmatch(current_line)
            is_inline = False
            
            if not match:
                match = compiled.search(current_line)
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
                    expanded.extend([(line_num, out_line) for out_line in output_lines])
                    matched_full = True
                    break
        
        if not matched_full:
            expanded.append((line_num, current_line))
    return expanded
