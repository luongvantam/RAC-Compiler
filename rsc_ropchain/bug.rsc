org 0xe9e0

def {tag} my_dummy_gadget : 0x1234

def add_hex(<val1>, <val2>) => eval(<val1> + <val2>)

add_hex(0x0001, 0x0002)
my_dummy_gadget

def nested_macros(<addr>, <val>) => {
    er0 = <addr>
    er2 = <val>
}

nested_macros(0xd730, 0x00aa)

def hello => {
    hex ff ff
    er0 = hex 00 00
}

hello

ea_switchcase