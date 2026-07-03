@section.main at 0xd630 backup 0xd8a0

lbl start
    hex 30 30 30 30       # xr4
    hex 30 80 30 02 2E D9 80 D1   # qr8
    mode_calc
    call 17502
    eval(adr(addr_input) + dist.main); hex 30 30    # xr8
    er2 = hex 60 00
    [er8]+=er2,pop xr8
    hex 30 30 c0 30
    pop xr0
    lbl addr_input
        hex 00 00
    hex 47 d9
    call 18932
    hex 60 00 30 30

lbl restore
    xr0 = adr(end), hex 60 30
    [er0]=r2
    xr0 = 0xd630, 0xd8a0
    hex e6 bf
    hex 30 d6
lbl end


@section.launcher at 0xd180

repeat 48 { hex 30 }
# mode 124an
xr0 = 0xd111, hex 02 30
[er0] = r2
xr0 = 0xd630, 0xd8a0
er14 = 0xd630
call 0x0bfe6
hex 5a 00