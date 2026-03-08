# format from `Segment:Addr  Opcode   Instruction`
# to `Instruction ; SegmentAddr | Opcode`

import re

def convert_disasm_file(input_path, output_path):
    line_regex = re.compile(
        r'^(\d):([0-9A-F]+)H\s+([0-9A-F]+)\s+(.+)$',
        re.IGNORECASE
    )

    with open(input_path, "r", encoding="utf-8") as infile:
        lines = infile.readlines()

    output_lines = []

    for line in lines:
        raw = line.rstrip("\n")

        if raw.endswith(":"):
            output_lines.append(raw + "\n")
            continue

        match = line_regex.match(raw.strip())
        if match:
            bank = match.group(1)
            addr = match.group(2).upper()
            opcode = match.group(3).upper()
            instruction = match.group(4).strip().lower()

            full_addr = f"{bank}{addr}"

            formatted = f"\t{instruction:<30} ; {full_addr} | {opcode}\n"
            output_lines.append(formatted)
        else:
            output_lines.append(line.lower())

    with open(output_path, "w", encoding="utf-8") as outfile:
        outfile.writelines(output_lines)

if __name__ == "__main__":
    file_input = input("name file format:")
    convert_disasm_file(file_input, "output.asm")