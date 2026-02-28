org 0xd630
# backup at 0xd8a0

dista = eval(0xd8a0-0xd630)

lbl start
    hex 30 30 30 30       # xr4
    hex 30 80 30 02 2E D9 80 D1   # qr8
    mode_calc
    call 17502
    eval(adr(addr_input) + dista); hex 30 30    # xr8
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

/*
34 7b 31 30 
11 D1 
02 30 
D2 03 32 30 
34 7b 31 30 
30 D6 
A0 D8 
62 0D 32 30 
30 D6 
E6 BF 
30 30 
5A 00
*/