# 
org 0xd730

lbl main
    er0 = adr(n)
    r0=[er0]
    call 16CA6     # r0-0x94_le,r0=1|r0=0,rt
    r1=0,rt
    er2 = adr(table)
    load_table
    er14 = er0, pop xr0
    hex 00 00 00 00
    sp = er14,pop er14

lbl false
    er2 = adr(n)
    er0=[er2],r2=9,rt
    er2=er0,er0+=er4,rt
    er0= hex 00 01
    er0-=er2,rt
    er2=eval(adr(if_yin)+0x1)
    hex_to_dec
    goto print

lbl true
    xr0 = adr(n), adr(if_yang)
    r0=[er0]
    hex_to_dec

lbl print
    er0 = er2,rt
    er2 = var_a
    calc_func
    
    line_print(0x1, 0x1, adr(n))
    render()
    brk

lbl n
    hex 64 00

lbl if_yin
    hex A7 00 00 00 00 00

lbl if_yang
    hex 00 00 00 00

# yin yang =)))
