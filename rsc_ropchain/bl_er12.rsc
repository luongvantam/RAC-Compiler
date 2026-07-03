def bl [er12+=r0]: 0x11976

@section.main at 0xd730

lbl main
    setlr_pc
    setsfr
    pop xr0
    hex 05 00
    hex 02 00
    er0 - er2_eq,r0 = 1|r0 = 0,rt
    er2 = er0,er0 = er2,pop er8,rt
    hex 00 00
    er0 += er2,rt                               # tương đương er0 += er0 hay er0*=2
    xr12 = adr(table), eval(adr(true) - 0x2)
    BL [er12+=r0]                               
    # nếu r0 = 0 thì gadget 11976 này sẽ trở thành 10742 ngược lại r0 = 1 sẽ trở thành 10740
    eval(adr(false) - 0x2)      # nếu r0 = 0 thì dòng này sẽ thành er14 vì 10742 là pop er14
    sp = er14, pop er14

lbl true
    xr0 = hex 01 01, adr(text1)
    line_print
    render.ddd4
    brk

lbl false
    xr0 = hex 01 01, adr(text0)
    line_print
    render.ddd4
    brk

lbl text1
    "True"
    hex 00 00

lbl text0
    "False"
    hex 00

lbl table
    hex 42 07
    hex 40 07

@section.launcher at 0xd180

hex fd 24
adr(main, -0x2)         # tương đương với eval(adr(main) - 0x2)
sp = er14, pop er14