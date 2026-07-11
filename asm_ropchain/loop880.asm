org 0xa830 # backup at 0xe300

lbl start
    # ...

restore_loop:
    di,rt
    er10 = adr_of length
    er0 = hex 01 00
    [er10] = er0,r0 = 0,pop xr8
    hex 00 00 00 00
    qr0 = adr_of start, adr_of [+15056] start, pr_length, adr_of [-2] start
    hex E6 4D
length:
    adr_arith end - adr_arith length
    hex 00 00
set_sp:
    sp = er6,pop er8

lbl end
    hex 00 00 00 00