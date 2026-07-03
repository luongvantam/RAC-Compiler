import sys, os, argparse, json, engine, io, contextlib
from extensions import expand_extensions_in_program, load_extensions
from loader import get_disassembly, get_commands

def resolve_file(name):
    if not name: return None
    for p in [os.path.join(d, f"{name}{ext}") for d in ("rsc_ropchain", "asm_ropchain", ".") for ext in ("", ".rsc", ".asm")]:
        if os.path.exists(p) and not os.path.isdir(p): return p

def main():
    parser = argparse.ArgumentParser(description="RAC Compiler")
    parser.add_argument('model', nargs='?', default='.', help='Model folder')
    parser.add_argument('input_name', nargs='?', help='Input file name')
    args, _ = parser.parse_known_args()
    
    if not args.input_name or args.model == '.':
        if len(sys.argv) < 3: sys.exit("Usage: python run.py <model> <name>")
        args.model, args.input_name = sys.argv[1:3]
        
    if not (file_path := resolve_file(args.input_name)): sys.exit("File not found in search paths.")
    config_file = os.path.join(args.model, "config.json")
    if not os.path.exists(config_file): sys.exit(f"Error: Config not found at {config_file}")
        
    config = json.load(open(config_file, "r", encoding="utf-8"))
    get_disassembly(os.path.join(args.model, config["disassembly_file"]))
    get_commands(os.path.join(args.model, config["gadgets_file"]), os.path.join(args.model, config["labels_file"]))
    ext_list = load_extensions(os.path.join(args.model, config["extensions_file"]))
    
    raw_content = open(file_path, "r", encoding="utf-8").read().splitlines()
    args.input_file, args.source_file = file_path, os.path.abspath(file_path)

    try:
        import handle_build_command as hbc
        build_config, raw_content = hbc.parse_build_block(raw_content)
        build_config.setdefault("emu.inj_var", os.path.splitext(os.path.basename(file_path))[0])
    except ImportError: build_config, hbc = {}, None

    program = expand_extensions_in_program(raw_content, ext_list)
    
    if build_config and hbc:
        f = io.StringIO()
        with contextlib.redirect_stdout(f): results = engine.process_program(args, program, config["overflow_initial_sp"])
        hbc.handle_build_output(build_config, results, f.getvalue())
    else: engine.process_program(args, program, config["overflow_initial_sp"])

if __name__ == "__main__":
    try: main()
    except EOFError: print("Error: stdin closed.")
