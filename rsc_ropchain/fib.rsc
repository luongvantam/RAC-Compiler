@section.main at 0xd730 backup 0xe9e0

/*
var_a = 0
var_b = 1
var_c = 0
var_x = n
*/

@build {
    line.gadgets = 0x30300000
}

lbl start
    setlr
    setsfr
    clear()

lbl main
    xr0 = adr(addr_calc_c), var_c
    calc_func
    xr0 = adr(addr_calc_a), var_a
    calc_func
    xr0 = adr(addr_calc_b), var_b
    calc_func
    xr0 = adr(addr_calc_x), var_x
    calc_func

lbl loop_n
    setlr
    er0 = var_x
    r0 = [er0]
    r1=0,rt
    er2 = hex 00 00
    er0 - er2_eq,r0 = 1|r0 = 0,rt
    er2 = adr(table)
    load_table
    er14 = er0, pop xr0
    hex 00 00 00 00
    sp = er14,pop er14

lbl print
    xr0 = var_a, 0xd400
    num_to_str
    xr0 = hex 01 01, 0xd400
    line_print
    render.ddd4
    brk

lbl restore
    di,rt
    xr0 = 0xd184d630
    BL strcpy
    er14 = 0xd62e
    sp = er14,pop er14
    hex 00 00

lbl addr_calc_a
    adr(calc_a)

lbl addr_calc_b
    adr(calc_b)

lbl addr_calc_c
    adr(calc_c)

lbl addr_calc_x
    adr(calc_x)

lbl calc_a
    # A = B
    'B'
    hex 00

lbl calc_b
    # B = C
    'C'
    hex 00

lbl calc_c
    # C = A + B
    'A + B'
    hex 00

lbl calc_x
    # x -= 1
    'x - 1'
    hex 00

lbl table
    eval(adr(restore) - 0x2)
    eval(adr(print) - 0x2)

lbl end
    hex 00 00 00 00


@section.launcher at 0xd180

hex fd 24 30 30
setlr
setsfr
xr0 = 0xd730, 0xe9e0
call 09451
hex fe 01
er14 = 0xd72e
sp = er14, pop er14
