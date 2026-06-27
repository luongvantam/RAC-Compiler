# launcher in 0xd180:FD 24 30 30 A8 9F 30 30 E0 A0 30 30 34 7b 31 30 30 d7 e0 e9 51 94 30 30 FE 01 78 5C 31 30 2e D7 60 0D 32 30
org 0xd730
lbl cursor_no_flash
    xr0 = hex 13 d1 01 00
    [er0]=r2              # store 0x1 to addr 0xd113
    
lbl setupkey
    er0 = adr(key)
    getscancode
    xr12=adr(table),adr(table)
    setlr
    call 17CA6
    pop er0
    lbl key
        hex 00 00
    call 09C20
    call 1C64A
    sp = er6, pop er8

lbl key_1_func
    xr0 = hex 21 30, adr(text1)
    printline 
    render.ddd4
    er14=eval(adr(loop)-0x2)
    sp=er14, pop er14

lbl key_2_func
    xr0 = hex 21 30, adr(text2)
    printline
    render.ddd4

lbl loop
    xr0 = 0xd184d630
    BL strcpy
    er14 = 0xd62e
    sp = er14,pop er14

lbl text1
    "aaaaaaaaaaaaa"
    0x00

lbl text2
    "bbbbbbbbbbbbb"
    0x00

lbl table
    hex 00 00 00 00 00 00 00 00 00 00
    KEY_1                       # if key = KEY_1
    eval(adr(key_1_func)-0x2)
    KEY_2                       # if key = KEY_2
    eval(adr(key_2_func)-0x2)
    hex 00 00                   # else
    eval(adr(loop)-0x2)















