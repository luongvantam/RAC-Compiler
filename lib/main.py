import sys, os, argparse, json, engine, io, contextlib
import loader, handlers, utils
from extensions import expand_extensions_in_program, load_extensions
from loader import get_disassembly, get_commands

def resolve_file(name):
    if not name: return None
    for p in [os.path.join(d, f"{name}{ext}") for d in ("rsc_ropchain", "asm_ropchain", ".") for ext in ("", ".rsc", ".asm")]:
        if os.path.exists(p) and not os.path.isdir(p): return p

def main():
    try:
        import check_update
        check_update.check_update(auto_mode=True)
    except Exception:
        pass

    parser = argparse.ArgumentParser(description="RAC Compiler")
    parser.add_argument('-u', '--update', action='store_true', help='Check and install updates')
    parser.add_argument('-s', '--safe', action='store_true', help='Safe mode (ignores local.txt and disables file outputs)')
    parser.add_argument('model', nargs='?', default='.', help='Model folder')
    parser.add_argument('input_name', nargs='?', help='Input file name')
    args, _ = parser.parse_known_args()
    
    if args.update:
        try:
            import check_update
            check_update.check_update(auto_mode=False)
        except Exception as e:
            print(f"Update failed: {e}")
        sys.exit(0)
    
    if not args.input_name or args.model == '.':
        clean_args = [a for a in sys.argv[1:] if not a.startswith('-')]
        if len(clean_args) < 2: raise utils.CompilerError("Usage: python run.py <model> <name>")
        args.model, args.input_name = clean_args[0:2]
        
    if not (file_path := resolve_file(args.input_name)): raise utils.CompilerError(f"File not found in search paths: {args.input_name}")
    config_file = os.path.join(args.model, "config.json")
    if not os.path.exists(config_file): raise utils.CompilerError(f"Config not found at {config_file}")
        
    try:
        config = json.load(open(config_file, "r", encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise utils.CompilerError(f"Invalid JSON in config file '{config_file}': {e}")
    except FileNotFoundError:
        raise utils.CompilerError(f"Config file not found at {config_file}")
    
    loader.char_to_hex.update(config.get("char_to_hex", {}))
    loader.token_to_hex.update(config.get("token_to_hex", {}))
    handlers.sorted_tokens = sorted(loader.token_to_hex.keys(), key=len, reverse=True)

    try:
        get_disassembly(os.path.join(args.model, config["disassembly_file"]))
        get_commands(os.path.join(args.model, config["gadgets_file"]), os.path.join(args.model, config["labels_file"]))
        ext_list = load_extensions(os.path.join(args.model, config["extensions_file"]))
    except KeyError as e:
        raise utils.CompilerError(f"Missing required key in config file: {e}")
    except FileNotFoundError as e:
        raise utils.CompilerError(f"File not found: {e.filename}")
    
    try:
        raw_content = open(file_path, "r", encoding="utf-8").read().splitlines()
    except Exception as e:
        raise utils.CompilerError(f"Error reading input file '{file_path}': {e}")
        
    args.input_file, args.source_file = file_path, os.path.abspath(file_path)

    try:
        import handle_build_command as hbc
        build_config, raw_content = hbc.parse_build_block(raw_content, safe_mode=args.safe)
        build_config.setdefault("emu.inj_var", os.path.splitext(os.path.basename(file_path))[0])
    except ImportError:
        build_config, hbc = {}, None
    
    loader.build_config = build_config
    loader.safe_mode = args.safe

    program = expand_extensions_in_program(raw_content, ext_list, safe_mode=args.safe)
    
    try:
        overflow_sp = config["overflow_initial_sp"]
    except KeyError:
        raise utils.CompilerError("Missing 'overflow_initial_sp' in config file.")

    if build_config and hbc:
        f = io.StringIO()
        with contextlib.redirect_stdout(f): results = engine.process_program(args, program, overflow_sp)
        hbc.handle_build_output(build_config, results, f.getvalue(), safe_mode=args.safe)
    else: 
        engine.process_program(args, program, overflow_sp)

if __name__ == "__main__":
    try: main()
    except EOFError: print("Error: stdin closed.")
    except Exception as e:
        import utils
        utils.report_error(e)
