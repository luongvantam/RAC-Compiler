@section.main at 0xd730 backup 0xe9e0

lbl p1render
lbl p1main
    setlr_pc
    di,rt
    pop qr0

lbl p1pointer
    # <-p1pointer>
    hex 00 d4 05 00; eval(adr(word)+dist.main); hex 00 00   # qr0
    r0=[er0]
    er0*=r2,er2=er0,er0+=er4,rt
    er2=er0,er0+=er4,rt
    pop er0

lbl p1pos
    # <-p1pos>
    hex 00 03   # er0
    line_print
    render.ddd4
    setlr_pc
    call 2840C      # er2=1,er0=er2,pop er8,rt
    adr(p1counterI)     # er8
    [er8]+=er2,pop xr8
    eval(adr(p1pos)+dist.main); hex 00 00   # xr8
    er2 = hex 30 00
    [er8]+=er2,pop xr8
    eval(adr(p1pointer)+dist.main); hex 00 00   # xr8
    er2=er0,er0+=er4,rt
    [er8]+=er2,pop xr8
    eval(adr(p1pos)+dist.main); hex 00 00   # xr8
    er14 = eval(adr(ac) + 0xe)

lbl p1counterI
    call 0981E
    hex 00 00; eval(adr(ac) + 0xe)      # xr12
    xr0 = hex 1E 00, adr(p1counterI)
    [er2]=r0,r0=0
    er2 = hex 40 0f
    [er8]+=er2,pop xr8
    adr(p1counterII); hex 00 00     # xr8
    er2 = hex 01 00
    [er8]+=er2,pop xr8
    adr(key); hex 00 00     # xr8

lbl p1counterII
    call 0981E
    hex 00 00 ; adr(p2main)     # xr12
    pop qr0
    hex 04 00; adr(mem)
    lbl adr_p3return
        adr(p3return)
    hex 01 00
    [er2]=r0,r2=0
    er2 = hex f5 d0
    [er2]=r0,r0=0
    er2 = eval(adr(p1pointer)+dist.main)
    [er2]=r0,r0=0


lbl p2readkey
    er0=er8
    getscancode
    setlr_pc
    setsfr
    call 10E80          # chú ý cái này
    adr(p2table); hex 00 00     # ea, er4

lbl key
    hex 11 45   # er6
    er0=er6,er2=er12
    ea_switchcase
    xr0 = eval(adr(p1pos)+dist.main), hex 00 03
    [er0]=er2,rt
    call 19E5A      # er8=[ea+]
    hex 72 1f     # from 21f72

lbl ac
    hex 02 00     # from 21f72
    xr0 = hex 00 d4 40 00
    memzero
    call 08BE0      # chắc clear
    pop qr8
    hex 50      # r8

lbl mem
    hex 00 e0 e9 30 d7; eval(adr(p1main) - 0xc)     # r9, er10, er12, er14
    er0=er8
    hex fe e1   # from 0E1FE

lbl up
    hex 00 00   # from 0E1FE
    hex 60 0d 02 00     # sp=er14,pop er14

lbl down
    hex 01 00
    hex 60 0d       # from 20d60

lbl right
    hex 02 00       # from 20d60
    hex 60 0d 02 00     # sp=er14,pop er14

lbl p2main
    hex 03 00

    qr0 = hex 11 45 10 00, adr(update), hex 01 00
    er0=er8
    er0*=r2,er2=er0,er0+=er4,rt
    er2=er0,er0+=er4,rt
    pop er0, pop er4
    adr(p3loader); hex 00 00   # er0, er4
    [er0]=er2,rt
    call 10E80          # chú ý cái này
    adr(p3table)    # ea 


lbl p3counter
    hex 04 00 00 fa     # xr4

lbl p3_update
lbl p3
    pop xr0

lbl p3loader
    hex 11 45 ; eval(adr(p3table) + 0x4)    # xr0
    er8=[er0],rt
    er0+=er4,rt
    r0=[er0]
    call 14fcc    # er0+=er6,er10=er0,rt
    call 16E18      # r4=0
    er4+=er0,r8=r8,rt
    r0=[er0]
    [er2]=r0,r0=0
    er0=er4,pop er4
    hex 00 00   # er4
    er0+=er8,rt
    er4+=er0,r8=r8,rt
    r0=[er0]
    ea_switchcase
    call 19E5A      # er8=[ea+]
    xr0 = adr(p3control), hex 00 00
    er2+=er8,rt
    [er0]=er2,rt
    er0=er10,pop xr8
    adr(p3counterI); hex 00 00  # xr8
    er10=er0,rt

lbl p3control
    hex ff ff 01 00
    eval(adr(p3next) - 0x2)     # er14 trong trường hợp er0 != các trường hợp đã cho (p3table)
    hex 60 0d 02 00     # sp=er14,pop er14
    hex aa bb cc dd        # cái này thêm để +sp không lệch
    er0 = hex 01 00
    call 1D3C8    # sp+=4
    r0=[er0]
    er8=er0
    er0=er4,pop er4
    hex 00 00       # er4
    er2=er0,er0+=er4,rt
    r0=[er0]
    er0+=er8,rt
    [er2]=r0,r0=0
    er0=er10,pop xr8
    adr(p3counterI); hex 00 00  # xr8
    er2=er0,er0+=er4,rt
    call 09C28    # er0=0
    [er2]=r0,r0=0

lbl p3next
    er2 = hex 01 00
    er14 = eval(adr(p3) - 0x16)
    [er8]+=er2,pop xr8
    adr(p3counter); hex 00 00   # xr8
    er2 = hex 01 00
    [er8]+=er2,pop xr8
    adr(p3near)     # er8

lbl p3near 
    adr(p3return)     # er10

lbl p3counterI
    call 21100          # loop cho đến khi nó là 2110C (pop xr4,pop qr8) thì chạy đoạn bên dưới

lbl p3return
    adr(p3for); hex 3e 9D; eval(adr(adr_p3return)+dist.main); hex 01 00    # xr4 and xr8
    [er8]+=er2,pop xr8
    hex 72 1f 02 00     # sp=[er8],pop er8
    er0 = eval(adr(p3) - 0xe)
    er14=er0,pop xr0
    hex 04 00; adr(p3counter)   # xr0
    [er2]=r0,r0=0
    qr0 = hex 00 00, adr(p3counterI), hex 00 00 01 00
    [er2]=r0,r0=0

lbl p3for
    call 0981F
    hex 00 00 00 00     # xr12

lbl p4_generate
    xr0 = adr(calc), hex 00 d5
    calc_func
    pop qr0
    hex 00 d5; adr(p4counter)      # xr0
 
lbl p4baseI
    # <-p4baseI>
    eval(adr(p4write) - 2); adr(p4check)    # xr4
    r0=[er0]
    [er2]=r0,r0=0

lbl p4back
    setlr_pc
    pop qr0

lbl p4counter
    hex 45 00 02 00; eval(adr(p4baseI)+dist.main)    # xr0, er4

lbl je
    eval(adr(ac) + 0xc)     # er6
    call 1428C
    call 1DD52
    # r0-0_ne,r0=1|r0=0,rt
    er0*=r2,er2=er0,er0+=er4,rt
    er8=er0
    sp=[er8],pop er8

lbl p4write
    qr0 = hex 11 45, adr(p4pos), hex ff ff, eval(adr(ac) + 0xc)
    er0=[er2],r2=9,rt
    er0+=er4,rt
    er2 = hex 01 00
    [er0]=r2
    call 09c28      # er0=0
    sp=er6,pop er8

lbl p4check
    adr(p4counter)      # er8
    pop xr0

lbl p4pos
    hex 00 d4 ff 2b     # xr0
    r0=[er0]
    call 1428C
    call 1DD52
    # r0-0_ne,r0=1|r0=0,rt
    er0+=er2,rt
    er2=er0,er0+=er4,rt
    [er8]+=er2,pop xr8
    adr(p4pos)      # er8

lbl t6
    eval(adr(ac) + 0x10)    # er10
    er2 = hex 01 00
    [er8]+=er2,pop xr8

lbl p4baseII
    eval(adr(p4back) - 0x2); adr(p4reset)     # xr8
    qr0 = adr(p4pos), hex 02 00, adr(p4baseII), hex f0 ff
    r0=[er0]
    call 14Fcc    # er0+=er6,er10=er0,rt
    call 1428C
    call 28FB2
    # r0-0_ne,r0=0|r0=1,rt
    er0*=r2,er2=er0,er0+=er4,rt
    er8=er0
    sp=[er8],pop er8

lbl p4reset
    adr(je)     # er8
    xr0 = hex 00 00, adr(p4pos)
    [er2]=r0,r0=0
    sp=[er8],pop er8

lbl calc
    hex 98 d1

lbl update
    hex fc ff 00 00
    hex 04 05 06 07 08 09 0a 0b 0c 0d 0e 0f
    hex 04 00 00 00
    hex 08 09 0a 0b 04 05 06 07 00 01 02 03
    hex 01 00 00 00
    hex 02 06 0a 0e 01 05 09 0d 00 04 08 0c
    hex ff ff 00 00
    hex 01 05 09 0d 02 06 0a 0e 03 07 0b 0f

lbl p2table
    KEY_UP
    adr(t1)
    KEY_DOWN 
    adr(t2)
    KEY_RIGHT
    adr(t3)
    KEY_LEFT
    adr(t4)
    KEY_AC
    adr(t5)
    hex 00 00       # else
    adr(t6)

lbl p3table
    hex 00 d4 
    hex c2 60          # sp+=0x14
    hex 45 d4 
    hex d4 62          # sp+=0xa
    hex 00 00          # else
    hex ca 0c          # pop er14

lbl word
    # <-word>
    hex 00 00 

lbl t5
    adr(ac) 
    hex 00 32 
    hex 00 00 

lbl t4
    adr(p2main)
    hex 34 00 

lbl t3
    adr(right)
    hex 00 38 00 00 

lbl t2
    adr(down)
    hex 31 36 00 00 
    hex 00 33 32 00 

lbl t1
    adr(up)
    hex 36 34 00 00 00          # 64
    hex 31 32 38 00 00          # 128
    hex 32 35 36 00 00          # 256
    hex 35 31 32 00 00          # 512
    hex 31 30 32 34 00          # 1024
    hex 32 30 34 38 00          # 2048
    hex 34 30 39 36 00          # 4096
    hex 38 31 39 32 00          # 8192
    hex 31 36 38 34 00          # 1684
    hex 00 00 ff

lbl end
    hex 00 00 00 00 00 00 00 00


@section.main at 0xd180

hex fd 24 30 30
qr8 = hex 31 05 e0 e9 30 d7 24 d7
er0=er8
call 0E1FE          # src=0xe9e0, dest=0xd730, length=0x531, sp=er6+0xc=0xd724+0xc=0xd730
lbl calc_random
    'Ran#'