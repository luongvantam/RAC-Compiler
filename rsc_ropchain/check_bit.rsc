@section.main at 0xd730

lbl input
    setlr_pc
    er0 = hex 22 22
    pixel_draw_black

lbl main
    xr0 = hex 31 30, 0xd400
    call 094C8
    brk

    r2 = r0,pop er0
    var_a
    setlr_pc
    num_frombyte
    
    pop er0
    lbl output
        hex 00 00
    r0 = [er0]
    
    r2 = r0,pop er0
    var_b
    setlr_pc
    num_frombyte
    
    xr0 = adr(addr_check), var_c
    calc_func

    er0 = var_d
    num_to_hex

    brk
    # check bên biến D (1 hoặc 0)

lbl addr_check
    adr(check)

lbl check
    # có thể viết là `B // 2 ^( 7 - A ) mod 2 _` nhưng không đảm bảo output ok =))
    'Int( B // 2 ^( 7 - A ) ) mod 2 _ _'

@section.launcher at 0xd180
hex FD 24 
0xd72e
sp = er14, pop er14
