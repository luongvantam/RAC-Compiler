from . import loader
from .optimizer import byte_to_key, get_npress_adr, optimize_adr_for_npress

def get_rom(x):
    if isinstance(x, str):
        with open(x, 'rb') as f:
            loader.rom = f.read()
    elif isinstance(x, bytes):
        loader.rom = x
    else:
        raise TypeError

def find_equivalent_addresses(rom_data: bytes, address_queue: set):
    from collections import defaultdict
    comefrom = defaultdict(list)

    for i in range(0, len(rom_data), 2):  # BC AL
        if rom_data[i + 1] == 0xce:
            offset = rom_data[i]
            if offset >= 128:
                offset -= 256
            target_addr = i >> 16 | ((i + (offset + 1) * 2) & 0xffff)
            comefrom[target_addr].append(i)

    for i in range(0, len(rom_data) - 2, 2):  # B
        if (
                rom_data[i] == 0x00 and
                (rom_data[i + 1] & 0xf0) == 0xf0):
            target_addr = (rom_data[i + 1] & 0x0f) << 16 | rom_data[i + 3] << 8 | rom_data[i + 2]
            comefrom[target_addr].append(i)

    for i in range(0, len(rom_data) - 4, 2):  # BL / POP PC
        if (
                rom_data[i] == 0x01 and
                (rom_data[i + 1] & 0xf0) == 0xf0 and
                (rom_data[i + 4] & 0xf0) == 0x8e and
                (rom_data[i + 5] & 0xf0) == 0xf2):
            target_addr = (rom_data[i + 1] & 0x0f) << 16 | rom_data[i + 3] << 8 | rom_data[i + 2]
            comefrom[target_addr].append(i)

    ans = set()
    while address_queue:
        adr = address_queue.pop()
        if adr in ans:
            continue
        ans.add(adr)

        if adr in comefrom:
            address_queue.update(comefrom[adr])

    return ans

def optimize_gadget_from_rom(rom_data: bytes, gadget_bytes: bytes) -> set:
    assert len(gadget_bytes) % 2 == 0
    pending_addresses = set()
    
    for i in range(0, len(rom_data) - len(gadget_bytes) + 1, 2):
        if rom_data[i:i + len(gadget_bytes)] == gadget_bytes:
            pending_addresses.add(i)

    return find_equivalent_addresses(rom_data, pending_addresses)

def optimize_gadget(gadget_bytes: bytes) -> set:
    return optimize_gadget_from_rom(loader.rom, gadget_bytes)

def print_addresses(adrs, n_preview: int):
    adrs = list(map(optimize_adr_for_npress, adrs))
    for adr in sorted(adrs, key=get_npress_adr):
        keys = ' '.join(map(byte_to_key,
                            (adr & 0xff, (adr >> 8) & 0xff, 0x30 | adr >> 16)
                            ))
        print(f'{adr:05x}  {get_npress_adr(adr):3}    {keys:20}')

        i = adr & 0x3FFFE
        count = 0
        while count < n_preview and i < len(loader.disasm):
            opcode = loader.disasm[i]
            if opcode != 0:
                label_name = loader.labels.get(i, "")
                label_str = f" <{label_name}>" if label_name else ""
                
                print(f'    {i:05x}: {opcode:04x}{label_str}')
                count += 1
            i += 2