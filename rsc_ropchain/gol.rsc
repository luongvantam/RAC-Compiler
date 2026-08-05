@section.main at 0xd730 backup 0xe9d4

lbl memcpy
    pop qr8
    hex 60 04
    0xe9d4
    0xd730

lbl ac
    eval(adr(keyread) - 0xC)
    er0 = er8
    call 0CD8A

lbl init
    setlr_pc
    DI,RT
    buffer_clear
    setsfr
    xr0 = eval(adr(pos) + dist.main), hex 60 1f
    [er0] = er2,rt
    xr0 = 0xd138, hex 03 01
    [er0] = er2,rt
    xr0 = hex 06 00 34 f0
    [er2] = r0,r2 = 0
    xr0 = hex 4f 0e 22 22
    call 08B2A
    xr0 = hex 50 0f 20 20
    call 08B2A

lbl keyread
    pop er0,pop er4
    adr(key)
    adr(keyhandle, -0x3e)
    call 2A9DA          # getscancode_nodelay
    setlr_pc
    pop qr0
    lbl flushcounter
        hex 00 00
        hex fe ff
    hex 00 03
    hex 66 87
    r0 &= r5, pop r4, rt
    hex 00 00
    call 2642E
    call 16CC0
    call 08F5A
    call 1DA70
    er2 = hex 0c 00
    er0 *= r2,er2 = er0,er0 += er4,rt
    call 14F02
    call 0a054
    setlr_pc
    pop xr0
    eval(adr(flushcounter) + dist.main)
    lbl flushctrl
        hex 01 00
    er8 = er0
    [er8] += er2,pop xr8
    hex 00 00 00 00

lbl keyhandle
    er6 = hex 01 00
    pop ea,pop xr4
    eval(adr(keytable) + dist.main)
    hex 00 00

lbl key
    hex 11 45
    er0 = er6,er2 = er12
    ea_switchcase
    er6 = [ea+]
    xr0 = eval(adr(pos) + dist.main), hex 45 11
    er2 += er8,rt
    er8 = er0
    [er8] += er2,pop xr8
    hex 00 00 00 00
    xr0 = eval(adr(keytable) + dist.main), adr(key)
    BL memcpy,pop er0
    hex 02 00
    xr0 = hex 00 d2 00 05
    memzero
    setlr_pc

    hex 38 1d

lbl setflush
    call 16132          # er14 = er0, pop xr0     chắc để lấy segment cho 361d ở trên
    eval(adr(flushcounter) + dist.main)
    hex 00 00
    [er0] = er2,rt
    xr0 = eval(adr(flushctrl) + dist.main), hex 03 00
    er8 = er0
    [er8] += er2,pop xr8
    adr(near1)

lbl near1
    adr(memcpy, -2)

    hex 36 1d

lbl setpx
    call 130e2      # pop qr0
    lbl pos
        hex 60 1f
    hex 01 01
    hex 66 66
    adr(memcpy, -2)
    call 08B2A

    hex 38 1d

lbl mouse
    call 16132          # er14 = er0, pop xr0
    hex d4 e3
    hex 00 06
    memzero
    setlr_pc
    pop qr0
    hex 00 00
    hex 39 d1
    hex 00 00
    adr(memcpy, -2)
    [er2] = r0,r2 = 0
    er2 = eval(adr(pos) + dist.main)
    er0 = [er2],r2 = 9,rt
    call 174F8
    pixel_draw
    pop xr0
    hex 01 00
    hex 39 d1
    [er2] = r0,r2 = 0

    hex 38 1d

lbl funcplus
    call 16132          # er14 = er0, pop xr0
    adr(funcdata)
    lbl funcpos
        hex 00 00
    call 13AA6
    pop er0
    lbl funcpointer
        hex 23 d2
    er0 += er8,rt
    er8 = er0
    r0 = [er0]
    call 08FD4
    er2 = er0,er0 += er4,rt
    er0 = er8
    [er0] = r2
    call 23E7A          # er0 = er2 = 1, pop er8, rt
    adr(funccounter)
    [er8] += er2,pop xr8
    adr(funcpos)
    hex 00 00
    er2 = hex 02 00
    [er8] += er2,pop xr8

lbl braddrI
    adr(calc, -2)
    adr(branchI, -2)
    er14 = adr(funcplus, -4)

lbl funccounter
    call 08B0E
    lbl braddrII
        adr(bitupdate, -2)
        adr(funcplus, -2)
    xr0 = hex 0e 00, adr(funccounter)
    [er2] = r0,r2 = 0
    er0 = adr(funcpos)
    [er0] = r2

lbl bitupdate
    call 23E7A          # er0 = er2 = 1, pop er8, rt
    adr(bit)
    [er8] += er2,pop xr8
    adr(funcpointer)
    hex 00 00
    er2 = 1,r0 = r2,rt
    [er8] += er2,pop xr8
    hex 00 00 00 00
    DI,RT
    pop qr0
    hex 00 00
    adr(bit)
    adr(braddrI)
    hex cc 24           # [10000 - $bitend]
    er0 = [er2],r2 = 9,rt
    call 14F02
    call 24A20
    call 1763C
    er0 *= r2,er2 = er0,er0 += er4,rt
    er8 = er0

    hex 36 1d

lbl branchI
    call 16132          # er14 = er0, pop xr0
    adr(bit)
    adr(bitdata)
    [er0] = er2,rt
    call 23E7A          # er0 = er2 = 1, pop er8, rt
    adr(pointer)
    [er8] += er2,pop xr8
    adr(loopI)
    hex 00 00
    er2 = 1,r0 = r2,rt
    [er8] += er2,pop xr8

lbl braddrIV
    adr(skipborder)
    adr(update, -2)
    ea_switchcase
    call 19BF0
    call 21d36

lbl branchIII
    pop qr0
    hex 00 00
    adr(pointer)
    adr(braddrIV)
    hex 00 00
    er0 = [er2],r2 = 9,rt
    call 0902E          # pop er2
    hex ce 1d           # [10000 - e232]
    call 08F5A
    call 24A20
    call 1763C
    er0 *= r2,er2 = er0,er0 += er4,rt
    er8 = er0
    sp = [er8],pop er8

lbl skipborder
    adr(funcpointer)
    xr0 = adr(loopI), hex fc ff
    [er0] = er2,rt
    er2 = hex 02 00
    [er8] += er2,pop xr8
    adr(pointer)
    hex 00 00
    er2 = hex 14 00
    [er8] += er2,pop xr8
    hex 00 00 00 00

lbl calc
    pop qr0
    lbl bit
        adr(bitdata)
        adr(realbit)
        hex 00 00
        hex 01 00
    pop ea,pop xr4
    adr(loopI)

lbl 1
    adr(branchIII, -2)

lbl 2
    adr(calc, -2)
    r0 = [er0]
    [er2] = r0,r2 = 0
    call 19168
    hex 00
    lbl realbit
        hex 01
    pop er0
    lbl pointer
        hex 46 df
    r0 = [er0]
    r0 &= r5, pop r4, rt
    hex 00 00
    call 18654
    call 1DA70
    call 1763C
    call 19168
    adr(braddrII)
    er0 *= r2,er2 = er0,er0 += er4,rt
    er8 = er0

    hex 36 1d

lbl clear
    call 130e2      # pop qr0
    adr(ac)
    adr(init, -0xc)
    hex 11 45
    adr(memcpy, -2)
    [er0] = er2,rt

    hex 38 1d

lbl update
    hex e2 30
    hex 01 00

lbl updatepos
    hex 23 d2 00 00 00 00 01 00
    r0 = [er0]
    call 2642E
    pop ea,pop xr4
    adr(updata)
    hex 00 00
    hex 00 00
    ea_switchcase
    er6 = [ea+]
    call 174F8
    hex 38 1d 02 00

lbl braddrV
    call 1763C
    pop er0

lbl screenpos
    hex 50 0f
    call 0850A
    hex 00 00
    hex 01 00

lbl returnloop
    call 23E7A
    adr(loopII)
    [er8] += er2,pop xr8
    adr(screenpos)
    hex 00 00
    er2 = 1,r0 = r2,rt
    [er8] += er2,pop xr8
    adr(updatepos)
    hex 00 00
    er2 = 1,r0 = r2,rt
    [er8] += er2,pop xr8
    hex 00 00
    hex 00 00
    pop ea,pop xr4
    adr(loopII)
    hex 00 00
    hex 00 00
    ea_switchcase
    er6 = [ea+]
    hex 38 1d 02 00

lbl loopreset
    pop xr0
    adr(loopII)
    hex e0 ff
    [er0] = er2,rt
    call 23E7A
    adr(loopII, +4)
    [er8] += er2,pop xr8
    adr(screenpos)
    hex 00 00
    call 0902E
    hex e0 00
    [er8] += er2,pop xr8
    adr(updatepos)
    hex 00 00
    call 0902E
    hex 02 00
    [er8] += er2,pop xr8
    adr(nearI)

lbl nearI
    adr(update, -2)
    sp = [er8],pop er8

lbl loopI
    hex fc ff
    adr(1)
    hex 00 00
    adr(2)

lbl loopII
    hex e0 ff
    adr(loopreset, -2)
    hex e0 ff
    adr(memcpy, -2)
    hex 00 00
    adr(update, -2)

lbl funcdata
    hex dd ff
    hex de ff
    hex df ff
    hex ff ff
    hex 01 00
    hex 21 00
    hex 22 00
    hex 23 00

lbl bitdata
    hex 80 40
    hex 20 10
    hex 08 04
    hex 02 01
lbl bitend

lbl updata
    hex 02 00
    adr(screenpos)
    hex 03 00
    adr(braddrV, +2)
    hex 00 00
    adr(braddrV, -2)

lbl keytable
    hex 11 45
    adr(update, -2)
    hex bb ee

    hex 01 40
    adr(calc, -2)
    hex bb ee

    hex 80 04
    adr(mouse, -2)
    hex bb ed

    hex 40 08
    adr(mouse, -2)
    hex bb ef

    hex 80 08
    adr(mouse, -2)
    hex bc ee

    hex 40 04
    adr(mouse, -2)
    hex ba ee

    hex 80 10
    adr(setpx)
    hex bb ee

    hex 80 02
    adr(setflush, -2)
    hex bb ee

    hex 04 10
    adr(clear, -2)
    hex bb ee

    hex 00 00
    adr(memcpy, -2)
    hex bb ee

@section.launcher at 0xd180
hex fd 24
0xe9d2
sp = er14, pop er14