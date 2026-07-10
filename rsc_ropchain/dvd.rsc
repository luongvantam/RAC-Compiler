@section.main at 0xd730 backup 0xe9e0

lbl render
    pop xr0
    lbl pos
        hex 18 14 80 16
    render_bitmap
    xr0 = hex 6e 64 00 00
    BL render.ddd4
    setlr_pc
lbl update_x
    er2 = hex 01 00
    er8 = adr(pos, 0, 0xe9e0)
    [er8]+=er2,pop xr8
    adr(pos, 0, 0xe9e0); hex 00 00
lbl update_y
    er2 = hex 00 01
    [er8]+=er2,pop xr8
    hex 00 00 00 00
lbl check_x
    er2 = adr(pos, 0, 0xe9e0)
    er0=[er2],r2=9,rt
    er8 = er0
    r1 = 0,rt
    ea = adr(table)
    cmp_ea
    qr0 = [ea]
    [er0] = er2, rt
lbl check_y
    er0 = er8
    r0 = 0
    ea = adr(table)
    cmp_ea
    qr0 = [ea]
    [er0] = er2, rt
lbl restore
    qr0 = 0xd630, 0xd184, 0x0000, 0xd62e
    BL strcpy
    sp = er6,pop er8
lbl table
    hex 40 00
    adr(update_x, 4, 0xe9e0); hex ff ff
    hex 01 00
    adr(update_x, 4, 0xe9e0); hex 01 00
    hex 00 2a
    adr(update_y, 4, 0xe9e0); hex 00 ff
    hex 00 01
    adr(update_y, 4, 0xe9e0); hex 00 01
    hex 00 00
    hex 00 00 00 00

@section.launcher at 0xd180
hex fd 24 30 30
setlr_pc
setsfr
buffer_clear
qr0 = 0x02fe, 0xe9e0, 0xd730, 0xd72e
memcpy_indr
0x3030
sp = er6,pop er8