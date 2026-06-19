# -*- coding: utf-8 -*-
import sys, os, argparse, json
from lib.engine import process_program
from lib.extensions import expand_extensions_in_program, load_extensions
from lib.loader import get_disassembly, get_commands
from lib.optimizer import set_npress_array

# Setup Parser
parser = argparse.ArgumentParser(description="RAC Compiler")
parser.add_argument('-f', '--format', default='hex', choices=('hex',), help='Output format')
parser.add_argument('-p', '--preview-count', type=lambda x: int(x, 0), default=0, help='Number of instructions to preview')
parser.add_argument('-t', '--target', default='none', help='Target platform')
parser.add_argument('folder', nargs='?', default='.', help='Folder containing config.json and data files')
parser.add_argument('input_file', nargs='?', help='Input RSC file')

args, unknown = parser.parse_known_args()

# Load Config
folder_path = args.folder
config_file_path = os.path.join(folder_path, "config.json")

if not os.path.exists(config_file_path):
    print(f"Error: Configuration file not found at {config_file_path}")
    sys.exit(1)

with open(config_file_path, "r", encoding="utf-8") as f:
    config = json.load(f)

def get_path(filename):
    return os.path.join(folder_path, filename)

# Initialize Compiler Components (No ROM or symbols representation setup)
get_disassembly(get_path(config["disassembly_file"]))
get_commands(get_path(config["gadgets_file"]), get_path(config["labels_file"]))
ext_list = load_extensions(get_path(config["extensions_file"]))
disas_filename = get_path(config["disassembly_file"])

# Setup Font and Display
set_npress_array(config["NPRESS"])

# Main Execution
if __name__ == "__main__":
    try:
        if args.input_file:
            if not os.path.exists(args.input_file):
                print(f"Error: Input file not found: {args.input_file}")
                sys.exit(1)
            with open(args.input_file, "r", encoding="utf-8") as f:
                raw_content = f.read().splitlines()
            args.source_file = os.path.abspath(args.input_file)
        else:
            raw_content = sys.stdin.read().splitlines()
            args.source_file = None
        
        if not raw_content and not args.input_file:
            pass 
        
        try:
            import handle_build_command as handle_build_command
            build_config, raw_content = handle_build_command.parse_build_block(raw_content)
            if "emu.inj_var" not in build_config:
                if args.input_file:
                    build_config["emu.inj_var"] = os.path.splitext(os.path.basename(args.input_file))[0]
                else:
                    build_config["emu.inj_var"] = "out"
        except ImportError:
            build_config = {}

        program = expand_extensions_in_program(raw_content, ext_list)
        
        if build_config:
            import io
            import contextlib
            f = io.StringIO()
            with contextlib.redirect_stdout(f):
                results = process_program(args, program, config["overflow_initial_sp"])
            handle_build_command.handle_build_output(build_config, results, f.getvalue())
        else:
            process_program(args, program, config["overflow_initial_sp"])
    except EOFError:
        print("Error: Standard input closed unexpectedly.")