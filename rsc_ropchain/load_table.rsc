org 0xD830

lbl main
    er0 = hex 03 03
    er2 = hex 02 02
    setlr
    er0 - er2_gt,r0 = 0 |r0 = 1,rt      # r0 = 0 if er0 > er2 else 1
    r1 = 0,rt
    er2 = adr(table)
    load_table
    er14 = er0, pop xr0
    hex 30 30 30 30
    sp = er14,pop er14
    hex 00 00

lbl true
    er0 = 0xF840
    er2 = hex ff ff
    [er0]=er2,rt
    brk

lbl false
    er0 = 0xF840
    er2 = hex 10 10
    [er0]=er2,rt
    brk

lbl table
    eval(adr(true) - 0x2)
    eval(adr(false) - 0x2)



