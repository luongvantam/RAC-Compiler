import os, re

def load_extensions(path):
    if not os.path.exists(path):
        print(f"[WARN] No extension file found: {path}"); return []
    with open(path, "r", encoding="utf-8") as f:
        matches = re.findall(r"---syntax---\s*(.*?)\s*---output---\s*(.*?)\s*---(?:\n|$)", f.read(), re.DOTALL)
    return sorted([{
        "syntax": s.strip(), "output": [ln.strip() for ln in o.strip().splitlines() if ln.strip()],
        "compiled_pattern": re.compile(re.escape(s.strip()).replace(r"\{", "(?P<").replace(r"\}", ">.+?)"))
    } for s, o in matches], key=lambda x: len(x["syntax"]), reverse=True)

def expand_extensions_in_program(program_lines, extensions):
    expanded = []
    for idx, line in enumerate(program_lines):
        line = line.strip()
        if not line: continue
        matched_full = False
        for ext in extensions:
            compiled = ext["compiled_pattern"]
            is_inline = not (match := compiled.fullmatch(line))
            if is_inline: match = compiled.search(line)
            
            if match:
                outputs = []
                for out in ext["output"]:
                    for k, v in match.groupdict().items(): out = out.replace(f"{{{k}}}", str(v))
                    outputs.append(out)
                
                if is_inline and len(outputs) == 1: line = line[:match.start()] + outputs[0] + line[match.end():]
                else:
                    expanded.extend([(idx + 1, o) for o in outputs])
                    matched_full = True; break
        if not matched_full: expanded.append((idx + 1, line))
    return expanded
