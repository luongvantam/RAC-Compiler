# -*- coding: utf-8 -*-
import sys, os, argparse, json
from lib.engine import process_program
from lib.extensions import expand_extensions_in_program, load_extensions
from lib.loader import get_disassembly, get_commands, read_rename_list
from lib.rom_analyzer import get_rom, optimize_gadget, find_equivalent_addresses, print_addresses
from lib.font_mapper import set_font, set_npress_array, set_symbolrepr
from lib import loader


# Setup Parser
parser = argparse.ArgumentParser(description="RAC Compiler")
parser.add_argument('-f', '--format', default='key', choices=('hex', 'key'), help='Output format')
parser.add_argument('-p', '--preview-count', type=lambda x: int(x, 0), default=0, help='Number of instructions to preview')
parser.add_argument('-g', '--gadget-adr', type=lambda x: int(x, 0), help='Find equivalent addresses for a hex address')
parser.add_argument('-gb', '--gadget-bin', help='Find equivalent addresses for a hex string')
parser.add_argument('-gn', '--gadget-nword', type=lambda x: int(x, 0), default=0, help='Number of words for gadget search')
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

config_file_path = os.path.join(folder_path, "config.json")

with open(config_file_path, "r", encoding="utf-8") as f:
    config = json.load(f)

def get_path(filename):
    return os.path.join(folder_path, filename)

# Initialize Compiler Components
get_rom(get_path(config["rom_file"]))
get_disassembly(get_path(config["disassembly_file"]))
get_commands(get_path(config["gadgets_file"]))
read_rename_list(get_path(config["labels_file"]))
ext_list = load_extensions(get_path(config["extensions_file"]))
disas_filename = get_path(config["disassembly_file"])

# Setup Font and Display
FINAL_FONT = []
for row in config["FONT"]:
    FINAL_FONT.extend(row[:16])
while len(FINAL_FONT) < 256:
    FINAL_FONT.append(' ')

set_font(FINAL_FONT)
set_npress_array(config["NPRESS"])

ROMWINDOW = 0xd000

def fetch(addr):
    return loader.rom[addr] | (loader.rom[addr+1] << 8)

def get_symbol(x):
    low, high = x & 0xff, x >> 8
    if low == 0: return 0, b''
    LOOKUP = {0x00: (0x2432, 0x2612), 0xfa: (0x2360, 0x23E2), 0xfe: (0x2092, 0x2270), 0xfd: (0x1F72, 0x2032), 0xfb: (0x1E82, 0x1F22)}
    er2_base, er4_base = LOOKUP.get(high, (None, None))
    if er2_base is None: return 0, b''
    er2 = fetch(er2_base + low*2)
    r0_val = loader.rom[er4_base + low]
    r4, r0 = r0_val >> 4, r0_val & 0x0F
    if r0 == 0: return 0, b''
    if r4 != 15: er2 += r4
    result = bytearray()
    count = r0
    while count > 0 and er2 < ROMWINDOW:
        val = loader.rom[er2]
        result.append(val)
        er2 = (er2 + 1) & 0xFFFF
        if 4 <= val < 0xF0: count -= 1
    if r4 == 15:
        result.append(ord('(')); r0 += 1
    return r0, bytes(result)

symbols = [''.join(FINAL_FONT[b] for b in get_symbol(x)[1]) for x in range(0xf0)] + ['@']*0x10
set_symbolrepr(symbols)

# Main Execution
if __name__ == "__main__":
    if args.gadget_bin:
        print_addresses(optimize_gadget(bytes.fromhex(args.gadget_bin)), args.preview_count)
    elif args.gadget_nword > 0 and args.gadget_adr is not None:
        start_adr = args.gadget_adr
        end_adr = start_adr + args.gadget_nword * 2
        print_addresses(optimize_gadget(loader.rom[start_adr:end_adr]), args.preview_count)
    elif args.gadget_adr is not None:
        print_addresses(find_equivalent_addresses(loader.rom, {args.gadget_adr}), args.preview_count)
    else:
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
            
            program = expand_extensions_in_program(raw_content, ext_list)
            process_program(args, program, config["overflow_initial_sp"])
        except EOFError:
            print("Error: Standard input closed unexpectedly.")