import json

overflow_initial_sp=...
rom_file = "rom.bin"
disassembly_file = "disas.txt"
gadgets_file = "gadgets.txt"
labels_file = "labels.txt"
extensions_file = "extensions.txt"

FONT=[l.split('\t') for l in '''
...
'''.strip('\n').split('\n')]

NPRESS=(
    ...
)

data = {
    "overflow_initial_sp": overflow_initial_sp,
    "rom_file": rom_file,
    "disassembly_file": disassembly_file,
    "gadgets_file": gadgets_file,
    "labels_file": labels_file,
    "extensions_file": extensions_file,
    "FONT": FONT,
    "NPRESS": list(NPRESS)
}

with open("config.json","w",encoding="utf-8") as f:
    json.dump(data,f,indent=4,ensure_ascii=False)