font = []
font_assoc = {}
npress = []
symbolrepr = []

def set_font(font_):
    global font, font_assoc
    font = font_
    font_assoc = dict((c, i) for i, c in enumerate(font))

def from_font(st):
    return [font_assoc[char] for char in st]

def to_font(charcodes):
    return ''.join(font[charcode] for charcode in charcodes)

def set_npress_array(npress_):
    global npress
    npress = npress_

def set_symbolrepr(symbolrepr_):
    global symbolrepr
    symbolrepr = symbolrepr_