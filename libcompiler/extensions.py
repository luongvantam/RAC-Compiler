from libcompiler.i18n import t
import os, re

def load_extensions(path):
    if not os.path.exists(path):

        print(t("warn_no_extension", path=path)); return []
    with open(path, "r", encoding="utf-8") as f:
        matches = re.findall(r"---syntax---\s*(.*?)\s*(?:---logic---\s*(.*?)\s*)?---output---\s*(.*?)\s*---(?:\n|$)", f.read(), re.DOTALL)
    return sorted([{
        "syntax": s.strip(), "logic": l.strip(), "output": [ln.strip() for ln in o.strip().splitlines() if ln.strip()],
        "compiled_pattern": re.compile(re.escape(s.strip()).replace(r"\{", "(?P<").replace(r"\}", ">.+?)"))
    } for s, l, o in matches], key=lambda x: len(x["syntax"]), reverse=True)

def expand_extensions_in_program(program_lines, extensions, safe_mode=False):
    expanded = []
    for idx, raw_line in enumerate(program_lines):
        line = raw_line.strip()
        if not line: continue
        matched_full = False
        indent = raw_line[:len(raw_line) - len(raw_line.lstrip())]
        
        for ext in extensions:
            compiled = ext["compiled_pattern"]
            
            match = compiled.fullmatch(line)
            is_inline = False
            if not match:
                match = compiled.search(raw_line)
                is_inline = True
            
            if match:
                env = {}
                original_env = {}
                for k, v in match.groupdict().items():
                    original_env[k] = v
                    try: env[k] = int(v, 0)
                    except ValueError: env[k] = v
                    
                if ext.get("logic") and not safe_mode:
                    try:
                        exec(ext["logic"], {}, env)
                    except Exception as e:
                        from libcompiler import utils
                        utils.report_error(f"Extension logic error in '{ext['syntax']}': {e}")
                
                outputs = []
                for out in ext["output"]:
                    for k, v in env.items():
                        v_str = str(v)
                        if type(v) is int and k in original_env:
                            orig = str(original_env[k]).strip()
                            if orig.lower().startswith("0x"):
                                pad = max(1, len(orig) - 2)
                                v_str = f"0x{v:0{pad}x}" if orig.startswith("0x") else f"0X{v:0{pad}X}"
                            elif orig.lower().startswith("0b"):
                                pad = max(1, len(orig) - 2)
                                v_str = f"0b{v:0{pad}b}" if orig.startswith("0b") else f"0B{v:0{pad}B}"
                        out = out.replace(f"{{{k}}}", v_str)
                    outputs.append(out)
                
                if is_inline and len(outputs) == 1: 
                    raw_line = raw_line[:match.start()] + outputs[0] + raw_line[match.end():]
                    line = raw_line.strip()
                else:
                    expanded.extend([(idx + 1, indent + o) for o in outputs])
                    matched_full = True; break
        if not matched_full: expanded.append((idx + 1, raw_line))
    return expanded
