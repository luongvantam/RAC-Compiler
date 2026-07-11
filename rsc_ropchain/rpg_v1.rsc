@section.main at 0xd830 backup 0xeb40

lbl map at 0xea30

lbl start
    xr0 = adr(map), hex 2e 2e
    BL memset, pop er2
    hex 01 01
    setlr
    er2 = adr(cursor, dist.main)
    er0 = [er2],r2 = 9,rt
    er2 = hex 40 00
    [er0] = r2

lbl render
    xr0 = 0x08, 0x01, adr(map)
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

    er0 = adr(key)
    getscancode
    xr0 = adr(key), hex 0e 7b
    setlr
    cvt_keycode
    er8 = hex 1c 00
    r0 -= r8,pop er8,rt
    hex 00 00
    r1=0,rt
    er2 = adr(table, dist.main)
    load_table
    er2 = er0,er0 += er4,rt
    er8 = adr(key, dist.main)
    [er8] += er2,pop xr8
    hex 00 00 00 00
    xr0 = 0xd830, 0xeb40
    call 203c8
    er14 = 0xd820
    sp = er14,pop qr8,pop qr0

lbl cursor
    0xea35

lbl key
    hex 00 00

lbl table
    hex e0 ff
    hex 20 00
    hex 01 00
    hex ff ff