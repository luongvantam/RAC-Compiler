@section.main at 0xd730 backup 0xe9e0

lbl main
    setlr_pc
    setsfr
    clear()
    smallprint(0x08,0x01,eval(adr(line_1)+dist.main))
    xr0 = 0x08,0x09,eval(adr(line_2)+dist.main)
    smallprint
    xr0 = 0x08,0x11,eval(adr(line_3)+dist.main)
    smallprint
    xr0 = 0x08,0x19,eval(adr(line_4)+dist.main)
    smallprint
    xr0 = 0x08,0x21,eval(adr(line_5)+dist.main)
    smallprint
    xr0 = 0x08,0x29,eval(adr(line_6)+dist.main)
    smallprint
    xr0 = 0x08,0x31,eval(adr(line_7)+dist.main)
    smallprint
    xr0 = 0x08,0x39,eval(adr(line_8)+dist.main)
    smallprint
    render()
    er0 = adr(key)
    getscancode
    ea = adr(table_key)
    setlr
    pop er0
    lbl key
        0x0000
    call 09C20
    call 1C64A
    sp = er6, pop er8

lbl key_up
    er2 = hex f7 ff
    goto key_move

lbl key_down
    er2 = hex 09 00
    goto key_move

lbl key_left
    er2 = hex ff ff
    goto key_move

lbl key_right
    er2 = hex 01 00

lbl key_move
    er8 = eval(adr(cursor) + dist.main)
    [er8]+=er2,pop xr8
    0x30303030
    goto key_loop

lbl key_1
    er2 = hex CC 00
    goto key_write

lbl key_0
    er2 = hex CD 00
    goto key_write

lbl key_write
    er0 = eval(adr(cursor) + dist.main)
    er0 = [er0],pop xr8,rt
    hex 00 00 00 00
    [er0] = r2,rt

lbl key_loop
    di,rt
    xr0 = 0xd630, 0xd184
    BL strcpy
    er6 = 0xd62e
    sp=er6,pop er8

lbl cursor
    eval(adr(picture) + dist.main)

lbl table_key
    KEY_UP
    eval(adr(key_up) - 0x2)
    KEY_DOWN
    eval(adr(key_down) - 0x2)
    KEY_LEFT
    eval(adr(key_left) - 0x2)
    KEY_RIGHT
    eval(adr(key_right) - 0x2)
    KEY_1
    eval(adr(key_1) - 0x2)
    KEY_0
    eval(adr(key_0) - 0x2)
    hex 00 00
    eval(adr(key_loop) - 0x2)

lbl picture
    lbl line_1
        hex CD CD CD CD CD CD CD CD 00
    lbl line_2
        hex CD CD CD CD CD CD CD CD 00
    lbl line_3
        hex CD CD CD CD CD CD CD CD 00
    lbl line_4
        hex CD CD CD CD CD CD CD CD 00
    lbl line_5
        hex CD CD CD CD CD CD CD CD 00
    lbl line_6
        hex CD CD CD CD CD CD CD CD 00
    lbl line_7
        hex CD CD CD CD CD CD CD CD 00
    lbl line_8
        hex CD CD CD CD CD CD CD CD 00

hex 00 00 00 00

@section.launcher at 0xd180
hex FD 24 
hex 30 30
setlr_pc
xr0 = 0xd730, 0xe9e0        # dst, src
call 09451
hex fe 02       # size
er14 = 0xd72e
sp = er14, pop er14



