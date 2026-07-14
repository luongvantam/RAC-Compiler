from libcompiler.i18n import t
import os, re

def _parse_config_lines(lines, cfg):
    for part in lines:
        if not (part := part.split("#")[0].strip()) or "=" not in part: continue
        k, v = [x.strip() for x in part.split("=", 1)]
        if v in ("true", "false"): v = v == "true"
        elif v.startswith(('"','\'')) and v.endswith(('"','\'')): v = v[1:-1]
        else:
            try: v = int(v, 0)
            except ValueError: pass
        cfg[k] = v

def parse_build_block(raw_content, safe_mode=False):
    cfg = {}
    if not safe_mode and os.path.exists("local.txt"): _parse_config_lines(open("local.txt", "r", encoding="utf-8").read().replace("\n", ";").split(";"), cfg)
    
    text = "\n".join(raw_content)
    if m := re.search(r'@build\s*\{([^}]*)\}', text, re.DOTALL):
        _parse_config_lines(m.group(1).replace("\n", ";").split(";"), cfg)
        text = text[:m.start()] + text[m.end():]
        
    if 'line.gadgets' in cfg:
        from libcompiler import loader
        offset = cfg['line.gadgets']
        for cmd, (adr, tags) in loader.commands.items():
            loader.commands[cmd] = (adr + offset, tags)
        loader.gadgets_offset_applied = True
        
    return cfg, text.splitlines()

def handle_build_output(cfg, results, stdout_str, safe_mode=False):
    fmt_lines, lb = [], cfg.get("line.bytes")
    for ln in stdout_str.splitlines():
        if isinstance(lb, int) and lb > 0:
            if ":" in ln and not ln.startswith("Address"):
                addr, b_str = ln.split(":", 1)
                fmt_lines.append(addr.strip() + ":")
                toks = b_str.split()
                fmt_lines.extend(" ".join(toks[i:i+lb]) for i in range(0, len(toks), lb))
                continue
            elif not ln.startswith("=") and ln.strip() and all(len(c) <= 6 for c in ln.split()):
                toks = ln.split()
                fmt_lines.extend(" ".join(toks[i:i+lb]) for i in range(0, len(toks), lb))
                continue
        fmt_lines.append(ln)
        
    if final_out := "\n".join(fmt_lines): print(final_out)
    
    if safe_mode:
        return
        
    if cfg.get("output.file") and (fn := cfg.get("output.file_name")):
        open(fn, "w", encoding="utf-8").write(final_out + "\n")

        print(t("msg_output_written", file=fn))
        
    if cfg.get('emu.inj') and (ef := cfg.get('emu.inj_file')) and (ev := cfg.get('emu.inj_var')) and results:
        entries = [f"    {cfg.get(f'emu.inj_addr[{n}]', cfg.get(f'emu.inj_adr[{n}]', a)):#06x} = \"{' '.join(f'{x:02x}' if isinstance(x, int) else str(x) for x in b)}\"" for n, a, b in results]
        new_block = f"{ev} = {{\n" + ",\n".join(entries) + "\n}"
        
        inj_content = open(ef, 'r', encoding='utf-8').read() if os.path.exists(ef) else ""
        if re.search(rf'^{re.escape(ev)}\s*=\s*\{{.*?\}}', inj_content, re.M | re.S):
            inj_content = re.sub(rf'^{re.escape(ev)}\s*=\s*\{{.*?\}}', new_block, inj_content, flags=re.M | re.S)
        else:
            inj_content = inj_content.rstrip()
            inj_content += (",\n" if inj_content.endswith('}') else "\n" if inj_content else "") + new_block
            
        open(ef, 'w', encoding='utf-8').write(inj_content)

        print(t("msg_file_written", file=ef))
