@section.main at 0xd730
def num_to_hex : 1ed58

lbl main
    setlr_pc
    setsfr
    xr0 = adr(addr_calc), var_a
    calc_func
    xr0 = var_a, adr(text)
    num_to_hex
    [er2] = r0, r2 = 0
    xr0 = hex 01 01, adr(text)
    line_print
    render.ddd4
    brk

lbl text
    hex 00 00 00 00

lbl addr_calc
    adr(calcc)

lbl calcc
    '1 + 1'
    hex 00


@section.launcher at 0xd180

hex fd 24
adr(main, -0x2)
sp = er14, pop er14