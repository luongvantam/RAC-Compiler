org 0xe9e0

var verify_func = call 0x13344

lbl main
    xr0 = adr(addr_verify), var_a
    verify_func
    er0=var_a
    r0=[er0]
    r1=0,rt
    er2=adr(tbl)
    load_table
    er14=er0,pop xr0
    0x30303030
    sp=er14,pop er14

lbl true
    line_print(0x1,0x1,adr(text_1))
    render()
    brk

lbl false
    line_print(0x1,0x1,adr(text_2))
    render()
    brk

lbl tbl
    calc(adr(false)-0x2)
    calc(adr(true)-0x2)

lbl addr_verify
    adr(verify)

lbl verify
     hex 31 A5 32 00

lbl text_1
    "True"
    hex 00

lbl text_2
    "False"
    hex 00