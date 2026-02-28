org 0xd730

/*
var_a = 0
var_b = 1
var_c = 0
var_x = n
*/

dista = eval(0xe9e0-0xd730)

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

lbl calc_a
    # A = B
    hex 43 00

lbl addr_calc_b
    adr(calc_b)

lbl calc_b
    # B = C
    hex 44 00

lbl addr_calc_c
    adr(calc_c)

lbl calc_c
    # C = A + B
    hex 42 A6 43 00

lbl addr_calc_x
    adr(calc_x)

lbl calc_x
    # x = x - 1
    hex 48 A7 31 00

lbl table
    eval(adr(restore) - 0x2)
    eval(adr(print) - 0x2)

lbl end
    hex 00 00 00 00

/* launcher in 0xd180
FD 24 30 30 
A8 9F 30 30 
E0 A0 30 30 
34 7b 31 30 
30 d7 
e0 e9 
51 94 30 30 
FE 01
78 5C 31 30 
2e D7 
60 0D 32 30
*/