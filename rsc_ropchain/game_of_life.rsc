@section.main at 0xd730 backup 0xe9e0

lbl start
    setlr_pc
    setsfr
    xr0 = hex f5 d0 01 00
    [er0]=er2,rt

lbl render
    render.ddd4

lbl setup_key
    getkeycode
    setlr_pc
    ea = adr(normal_table)
    ea_cmp
    call 1C64A
    pop xr0
    lbl pos = hex 00 00 00 00
    er2+=er8,rt
    sp = er6, pop er8
    adr(gadgets_jump_clear)

lbl key_del
    [er8]+=er2,pop xr8
    eval(adr(addr_jump_in_key_del) + dist.main)                 # er8
    lbl addr_jump_in_key_del = eval(adr(key_loop) - 0x2)        # [er8] (er10)
    lbl gadgets_jump_clear = hex 00 00 00 00
    sp = [er8], pop er8

lbl key_draw
    call 0x091e6
    xr0 = 0xd400, adr(pos, dist.main)
    strcat

lbl key_move
    er2 = 0xd150
    er0 = [er2],r2 = 9,rt
    ea = adr(move_table)
    ea_cmp
    qr0=[ea],lea D002H,[ea]=qr0
    er2 = er0,er0 = er2,pop er8,rt
    adr(pos, dist.main)
    [er8]+=er2,pop xr8
    hex 00 00 00 00

lbl key_loop
    er6 = eval(adr(jump_to_start) - 0x2)
    sp = er6, pop er8

lbl main
    setlr_pc


lbl jump_to_start
    xr0 = adr(addr_jump_to_main), eval(adr(start) - 0x2)
    [er0]=er2,rt

lbl restore
    di,rt
    xr0 = adr(length), hex 01 00
    [er0]=er2,rt
    pop qr0
    pr_length; 0xe9e0; 0xd730
    lbl addr_jump_to_main
        adr(main, -2)
    hex 32 89
lbl length
    eval(adr(end) - adr(length))
    hex 00 00
    sp = er6, pop er8

lbl normal_table
    hex 30 fc
    eval(adr(key_draw) - 0x2)

    hex 3e fc
    eval(adr(key_del) - 0x2)
    0x91ea          # draw_pixel_white

    hex 26 fc
    eval(adr(key_del) - 0x2)
    0x8c60          # buffer_clear

    hex 00 00
    eval(adr(key_move) - 0x2)

lbl move_table
    KEY_LEFT
    hex ff 00

    KEY_RIGHT
    hex 01 00

    KEY_UP
    hex 00 ff

    KEY_DOWN
    hex 00 01

    0x0000         # else
    hex 00 00

lbl end
    hex 00 00 00 00

@section.launcher at 0xd180
org 0xd180
hex fd 24 30 30
qr0 = hex fe 01 e0 e9 30 d7 2e d7
call 18932
hex 30 30
sp = er6, pop er8