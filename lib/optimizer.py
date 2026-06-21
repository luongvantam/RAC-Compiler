# -*- coding: utf-8 -*-
max_call_adr = 0x3ffff
npress = []

def set_npress_array(npress_):
    global npress
    npress = npress_

def get_npress(charcodes):
    if isinstance(charcodes, int):
        charcodes = (charcodes,)
    return sum(npress[charcode] for charcode in charcodes)

def get_npress_adr(adrs):
    if isinstance(adrs, int):
        adrs = (adrs,)
    assert all(0 <= adr <= max_call_adr for adr in adrs)
    return sum(get_npress((adr & 0xFF, (adr >> 8) & 0xFF)) for adr in adrs)
