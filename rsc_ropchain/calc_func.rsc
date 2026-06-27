org 0xd730

setlr
di,rt
xr0 = adr(addr_calc), adr(result)
calc_func
xr0 = adr(result), hex 30 30
r0=[er0]
r1=0,rt

line_print(0x1, 0x1, adr(result))
render()
brk

lbl addr_calc
    adr(calc)

lbl calc
    # 1 + 2
    hex 31 A6 32

lbl result
    hex 00 00 00 00 00 00 00 00 00 00 00 00


