@section.main at 0xd730

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
    er14=eval(adr(restore)-0x2)
    sp=er14, pop er14

lbl key_2_func
    xr0 = hex 21 30, adr(text2)
    printline
    render.ddd4

lbl restore
    xr0 = 0xd630, 0xd184
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
    eval(adr(restore)-0x2)


@section.launcher at 0xd180

hex fd 24 30 30
setlr
setsfr
xr0 = 0xd730, 0xe9e0
call 09451
hex fe 01
er14 = 0xd72e
sp = er14, pop er14