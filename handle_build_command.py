import sys
import os
import re

def _parse_config_lines(lines, build_config):
    for part in lines:
        part = part.strip()
        if not part or part.startswith("#"): continue
        part = part.split("#")[0].strip()
        if "=" in part:
            k, v = part.split("=", 1)
            k = k.strip()
            v = v.strip()
            if v == "true": v = True
            elif v == "false": v = False
            elif v.startswith('"') and v.endswith('"'): v = v[1:-1]
            elif v.startswith("'") and v.endswith("'"): v = v[1:-1]
            else:
                try:
                    v = int(v, 0)
                except ValueError:
                    pass
            build_config[k] = v

def parse_build_block(raw_content):
    build_config = {}
    
    if os.path.exists("local.txt"):
        with open("local.txt", "r", encoding="utf-8") as f:
            local_lines = f.read().splitlines()
            local_str = "\n".join(local_lines).replace("\n", ";")
            _parse_config_lines(local_str.split(";"), build_config)
            
    new_raw_content = []
    in_build = False
    build_str = ""
    for line in raw_content:
        stripped = line.strip()
        if not in_build:
            if stripped.startswith("@build"):
                in_build = True
                build_str += line + "\n"
                if "{" not in stripped and ";" in stripped:
                    in_build = False
                elif "}" in stripped:
                    in_build = False
            else:
                new_raw_content.append(line)
        else:
            build_str += line + "\n"
            if "}" in stripped:
                in_build = False

    if build_str:
        build_str = build_str.replace("@build", "", 1).strip()
        if build_str.startswith("{"): build_str = build_str[1:]
        if build_str.endswith("}"): build_str = build_str[:-1]
        _parse_config_lines(build_str.replace("\n", ";").split(";"), build_config)
                
    return build_config, new_raw_content


def handle_build_output(build_config, results, stdout_str):
    """
    Handles line formatting, output to file, and emu injection.
    """
    line_bytes = build_config.get("line.bytes")
    formatted_lines = []
    
    # Format stdout_str if line.bytes is specified
    lines = stdout_str.splitlines()
    for line in lines:
        if line_bytes and isinstance(line_bytes, int) and ":" in line and not line.startswith("Address to load"):
            parts = line.split(":", 1)
            addr_str = parts[0].strip()
            bytes_str = parts[1].strip()
            tokens = bytes_str.split()
            
            formatted_lines.append(addr_str + ":")
            for j in range(0, len(tokens), line_bytes):
                formatted_lines.append(" ".join(tokens[j:j+line_bytes]))
            continue
        elif line_bytes and isinstance(line_bytes, int) and not line.startswith("=") and line.strip() and all(len(c) <= 6 for c in line.split() if c.isalnum() or True):
            tokens = line.split()
            for j in range(0, len(tokens), line_bytes):
                formatted_lines.append(" ".join(tokens[j:j+line_bytes]))
            continue
            
        formatted_lines.append(line)
        
    final_output = "\n".join(formatted_lines)
    
    # Print the formatted output back to real stdout
    if final_output:
        print(final_output)
    
    # Write to output file
    if build_config.get("output.file") and build_config.get("output.file_name"):
        with open(build_config["output.file_name"], "w", encoding="utf-8") as f:
            f.write(final_output + "\n")
            
        print(f"Output written to: {build_config['output.file_name']}")
            
    # Handle EMU Injection
    emu_inj = build_config.get('emu.inj', False)
    emu_inj_file = build_config.get('emu.inj_file')
    emu_inj_var = build_config.get('emu.inj_var')
    
    if emu_inj and emu_inj_file and emu_inj_var and results:
        var_content = []
        var_content.append(f"{emu_inj_var} = {{")
        entries = []
        
        for name, addr, b_list in results:
            override_key_1 = f"emu.inj_addr[{name}]"
            override_key_2 = f"emu.inj_adr[{name}]"
            override_addr = build_config.get(override_key_1, build_config.get(override_key_2))
            final_addr = override_addr if override_addr is not None else addr
            
            if isinstance(b_list, list) and all(isinstance(x, int) for x in b_list):
                hex_str = " ".join(f"{x:02x}" for x in b_list)
            else:
                hex_str = " ".join(f"{x:02x}" if isinstance(x, int) else str(x) for x in b_list)
                
            entries.append(f"    {final_addr:#06x} = \"{hex_str}\"")
            
        var_content.append(",\n".join(entries))
        var_content.append("}")
        
        new_block = "\n".join(var_content)
        
        if os.path.exists(emu_inj_file):
            with open(emu_inj_file, 'r', encoding='utf-8') as f:
                inj_content = f.read()
        else:
            inj_content = ""
            
        pattern = re.compile(rf'^{re.escape(emu_inj_var)}\s*=\s*\{{.*?\}}', re.MULTILINE | re.DOTALL)
        if pattern.search(inj_content):
            inj_content = pattern.sub(new_block, inj_content)
        else:
            inj_content = inj_content.rstrip()
            if inj_content.endswith('}'):
                inj_content += ",\n" + new_block
            else:
                if inj_content:
                    inj_content += "\n"
                inj_content += new_block
                
        with open(emu_inj_file, 'w', encoding='utf-8') as f:
            f.write(inj_content)

        print(f"File written successfully: {emu_inj_file}")