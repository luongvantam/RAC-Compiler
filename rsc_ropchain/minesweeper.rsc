@build {
    emu.inj = true
    emu.inj_file = "/Users/luongtoi/CasioEmuMsvc/hc-inj.txt"
    emu.inj_adr[main] = 0xe9d4
}

@section.main at 0xd730 backup 0xe9d4

lbl start
    xr0 = 0xe3e0, hex 30 30
    BL memset, pop er2
    hex 00 01

    xr0 = 0xd400, hex cc cc
    BL memset, pop er2
    hex 00 01

lbl setup_bom
    xr0 = eval(adr(loop_bom) + dist.main - 3870), eval(adr(table_bom) + dist.main)
    er0 = [er0 + 3870]
    call 1428C
    call 1E60A
    # 1428C + 1E60A thành r0-0_ne,er0=0|er0=1,rt
    er0+=er0,er2+=er0,er0=[er2]
    er14 = er0,pop xr0
    adr(adr_calc_random); var_ans
    sp = er14,pop er14

lbl table_bom
    adr(dat_bom, -2)
    adr(print_board, -2)

lbl dat_bom
    calc_func
    er0 = var_ans
    num_to_hex
    r1 = 0,rt
    er2 = 0xe3e0
    er0 += er2,rt
    er2 = hex 24 00
    [er0] = r2
    er8 = er0
    

lbl print_board
    setlr_pc
    xr0 = hex 08 01 00 d4
    smallprint
    er0 = hex 08 09
    smallprint
    er0 = hex 08 11
    smallprint
    er0 = hex 08 19
    smallprint
    er0 = hex 08 21
    smallprint
    er0 = hex 08 29
    smallprint
    er0 = hex 08 31
    smallprint
    er0 = hex 08 39
    smallprint
    render.ddd4
    
lbl get_key
    er0 = adr(key)
    getscancode
    pop er0
    lbl key
        hex 00 00
    ea = adr(table_key)
    ea_switchcase
    er6 = [ea+]
    er0 = er8
    sp = er6, pop er8

lbl update_cursor
    er2 = er0,er0 = er2,pop er8,rt
    eval(adr(cursor) + dist.main)
    [er8] += er2,pop xr8
    hex 00 00 00 00
    brk

lbl cursor
    0xd400

lbl loop_bom
    hex 0a 00

lbl table_key
    KEY_UP

    KEY_DOWN

    KEY_RIGHT


    KEY_LEFT

    KEY_SHIFT

    hex 00 00

@section.launcher at 0xd180
hex fd 20
0xd730
hex fe 02
lbl adr_calc_random
    adr(calc_random)
hex 30 30
0xe9d4
0xd724
setlr_pc
setsfr
xr0 = 0xd0f5, hex 30 30
[er0]=r2
memcpy_auto_jump
lbl calc_random
    'ranint#(0,255'