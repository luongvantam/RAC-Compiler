from functools import lru_cache
from . import font_mapper

max_call_adr = 0x3ffff

@lru_cache(maxsize=256)
def byte_to_key(byte):
    if byte == 0:
        return '<NUL>'

    # TODO hack for classwiz without unstable
    sym = font_mapper.symbolrepr[byte]
    return f'<{byte:02x}>' if sym in ('@', '') else sym

    offset = 0
    sym = font_mapper.symbolrepr[byte]
    while byte and font_mapper.npress[byte] >= 100:
        byte = byte - 1
        offset += 1
    typesym = font_mapper.symbolrepr[byte] if byte else 'NUL'

    if set(sym) & set('\'"<>:'):
        sym = repr(sym)
    if set(typesym) & set('\'"<>:+'):
        typesym = repr(typesym)

    if offset == 0:
        return sym
    else:
        return f'<{sym}:{typesym}+{offset}>'

def get_npress(charcodes):
    if isinstance(charcodes, int):
        charcodes = (charcodes,)
    return sum(font_mapper.npress[charcode] for charcode in charcodes)

def get_npress_adr(adrs):
    if isinstance(adrs, int):
        adrs = (adrs,)
    assert all(0 <= adr <= max_call_adr for adr in adrs)
    return sum(get_npress((adr & 0xFF, (adr >> 8) & 0xFF)) for adr in adrs)

def optimize_adr_for_npress(adr):
    '''
    For a 'POP PC' command, the lowest significant bit in the address
    does not matter. This function use that fact to minimize number
    of key strokes used to enter the hackstring.
    '''
    return min((adr, adr ^ 1), key=get_npress_adr)

def optimize_sum_for_npress(total):
    ''' Return (a, b) such that a + b == total. '''
    return ['0x' + hex(x)[2:].zfill(4) for x in min(
        ((x, (total - x) % 0x10000) for x in range(0x0101, 0x10000)),
        key=get_npress_adr
    )]