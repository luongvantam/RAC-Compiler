@section.main at 0xE3E0 backup 0xE630
getkey_er8 = call 2F5F0
in_bitmap_moi = call 09856

lbl main
    pop er0
lbl tbl_adr_inc
    hex 00 00
    xr12 = adr(tbl), eval(adr(jmp) - 2)
    call 11976      # BL [ER12+=R0]
    eval(adr(out) - 2)
    sp = er14,pop er14

lbl jmp
    er8 = eval(adr(tbl_adr_inc) + dist.main)
    er2 = 0x0002
    [er8] += er2,pop xr8
    hex 00 00 00 00

lbl restore
    DI,RT
    pop xr4,pop xr12
    adr(main); pr_length
    backup; eval(adr(main) - 0xC)
    memcpy_auto_jmp

lbl out
    brk
    
lbl tbl
    0x0740
    0x0740
    0x0740
    0x0742