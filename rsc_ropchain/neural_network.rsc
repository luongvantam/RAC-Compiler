/*
    8×8 Single-Neuron Neural Network for fx580vnx
    * Binary Digit Classifier (0 vs 1)
    * Accuracy: ~70–85%
    * Created by luongvantam
    * Use https://github.com/luongvantam/RAC-Compiler/ to compile this program.
*/

@build {
    emu.inj = true
    #emu.inj_file = "hc-inj.txt"
    emu.inj_adr[main] = 0xe9e0
}

@section.main at 0xd730 backup 0xe9e0

/*
sum_w = var_a
sum_n = var_b
z = var_c
threshold = var_d
w_now = var_e
n_now = var_f
*/

lbl start
    setlr_pc
    xr0 = eval(adr(var_i) + dist.main), 0xd0f5
    [er2]=r0,r2=0
    [er0]=r2
    xr0 = 0xd324, 0xdc90
    call 09451
    hex 46 00

lbl draw_picture
    call 23f84                          # pop qr8, pop qr0
    eval(adr(pos)+dist.main)            # er8
    hex 00 00                           # er10
    hex 00 08                           # er12
    eval(adr(jump_to_start) - 0x4)      # er14
    lbl pos
        hex 44 01                       # er0
    lbl adr_line
        eval(adr(line_1)+dist.main)     # er2
    eval(adr(counter_loop)+dist.main)   # er4
    hex 00 00                           # er6
    line_print
    er0 = er6,er2 = er12
    [er8] += er2,pop xr8
    eval(adr(adr_line)+dist.main); hex 00 00
    er2 = hex 09 00
    [er8] += er2,pop xr8
    adr(key); hex 00 00
    setlr_pc
    [er4]+=1,rt
    lbl counter_loop
        call 0981A
        eval(adr(table_key) - 0xa); eval(adr(table_key) - 0xa)      # xr12
    xr0 = eval(adr(counter_loop)+dist.main), hex 1a 98
    [er0]=er2,rt
    xr0 = eval(adr(pos)+dist.main), hex 44 01
    [er0]=er2,rt
    xr0 = eval(adr(adr_line)+dist.main), eval(adr(line_1)+dist.main)
    [er0]=er2,rt
    render()

lbl get_key
    er0 = er8
    getscancode
    setlr_pc
    # xr12 = eval(adr(table_key) - 0xa); eval(adr(table_key) - 0xa)
    call 17CA6
    pop er0
    lbl key
        hex 00 00
    call 09C20
    call 1C64A
    er0 = er8
    sp = er6, pop er8
    eval(adr(cursor) + dist.main)

lbl key_move
    er2=er0,er0+=er4,rt
    [er8]+=er2,pop xr8
    hex 00 00 00 00
    goto key_loop

lbl key_write
    er2=er0,er0+=er4,rt
    er0 = eval(adr(cursor) + dist.main)
    er0 = [er0],pop xr8,rt
    hex 00 00 00 00
    [er0]=r2

lbl key_loop
    er14 = eval(adr(jump_to_start) - 0x2)
    sp=er14,pop er14

lbl var_i
    hex 00 00

lbl main
    setlr_pc
    clear()
    qr0 = 0x3d, 0x1b, eval(adr(text_loading) + dist.main), hex 00 00 00 00
    line_print
    render()

lbl check_n
    setlr_pc
    xr0 = eval(adr(picture) + dist.main), hex cc 00
    er0+=er8,rt
    r0=[er0]
    r1=0,rt
    er0 - er2_eq,r0 = 1|r0 = 0,rt
    er2 = adr(var_n)
    hex_to_dec

lbl loop_w
    # var_w = var_w + weights[var_i] * picture[var_i]
    r2 = r0,pop er0
    eval(adr(weights) + dist.main)
    er0+=er8,rt
    r0 = [er0]
    # er0 = picture[var_i], er2 = weights[var_i]
    er0 *= r2,er2 = er0,er0 += er4,rt       # er2 = er0 = weights[var_i] * picture[var_i]
    er2 = adr(w_now)
    hex_to_dec
    xr0 = adr(addr_w_now), var_e
    calc_func
    xr0 = adr(addr_calc_sum), var_a
    calc_func

lbl loop_n
    #var_n = picture[var_i] + var_n
    xr0 = adr(addr_var_n), var_f
    calc_func
    xr0 = adr(addr_calc_sum_n), var_b
    calc_func

lbl store_y
    xr0 = adr(addr_calc_y), var_c
    calc_func

lbl store_threshold
    xr0 = adr(addr_calc_threshold), var_d
    calc_func

lbl loop_i
    # var_i += 0 if var_i == 72 else 1
    setlr_pc
    qr0 = eval(adr(var_i) + dist.main), 0x0048, eval(adr(add_i) - 0x2), hex 00 00
    r0 = [er0]
    r1=0,rt
    er0 - er2_eq,r0 = 1|r0 = 0,rt
    er2 = eval(adr(print_result) - adr(add_i))
    er0 *= r2,er2 = er0,er0 += er4,rt
    er14 = er0, pop xr0
    var_c; var_d
    sp = er14, pop er14
    eval(adr(restore) - 0x2)

lbl add_i
    er4 = eval(adr(var_i) + dist.main)
    [er4] += 1,rt
    sp=er14, pop er14

lbl print_result
    verify_gt
    /*
        if y > threshold:
            er0 = hex 00 01
            er2 = hex 01 00
        else:
            er0 = er2 = hex 00 00
    */
    setlr_pc
    clear()
    er0 = er2,rt
    er2 = adr(table_text)
    load_table
    er14 = er0, pop xr0
    hex 11 11
    adr(text_one)
    sp = er14,pop er14

lbl table_text
    eval(adr(if_num_is_zero) - 0x2)
    eval(adr(if_num_is_one) - 0x2)

lbl if_num_is_one
    er4 = adr(if_num_is_zero)
    [er4] += 1,rt   # if_num_is_zero: call 23EC2

lbl if_num_is_zero
    call 23EC1      # er2 += 4, bl line_print.col_0

lbl print_output
    xr0 = 0x0101, eval(adr(tilte) + dist.main)
    call 23EC2
    xr0 = 0x0909, eval(adr(text) + dist.main)
    call 23EC2
    xr0 = 0x3939, eval(adr(text_cre) + dist.main)
    call 23EC2
    render.ddd4
    waitshift
    setlr_pc
    clear()
    lbl jump_to_start
        xr0 = adr(addr_jump_to_main), eval(adr(start) - 0x2)
        [er0]=er2,rt

lbl restore
    di,rt
    xr0 = adr(length), hex 01 00
    [er0]=er2,rt
    pop qr0
    pr_length; 0xe9e0; 0xd730
    lbl addr_jump_to_main
        adr(main, -2)
    hex 32 89
lbl length
    eval(adr(end) - adr(length))
    hex 00 00
    sp = er6, pop er8

lbl addr_calc_y
    adr(calc_y)

lbl addr_calc_threshold
    adr(calc_threshold)

lbl addr_calc_sum
    adr(calc_sum_w)

lbl addr_var_n
    adr(var_n)

lbl addr_calc_sum_n
    adr(calc_sum_n)

lbl addr_w_now
    adr(w_now)

lbl calc_y
    'A / 2 - 1 0 0 * B'     # var_c
    hex 00

lbl calc_threshold
    '3 3 3 3'       # var_d
    hex 00

lbl calc_sum_w
    'E + A'         # var_a
    hex 00

lbl var_n
    hex 00 00 00
    # var_f

lbl calc_sum_n
    'F + B'         # var_b
    hex 00

lbl w_now
    hex 00 00 00 00
    # var_e

lbl tilte
    "NEURAL NETWORK"
    hex 00

lbl text
    "this is"
    hex 00

lbl text_one
    hex 31 00 00 00

lbl text_zero
    hex 30 00

lbl text_cre
    "cre:@luongvantam"
    hex 00

lbl text_loading
    "loading... "
    hex 00

lbl cursor
    eval(adr(picture) + dist.main)

lbl table_key
    KEY_UP
    eval(adr(key_move) - 0x2)
    hex f7 ff
    KEY_DOWN
    eval(adr(key_move) - 0x2)
    hex 09 00
    KEY_LEFT
    eval(adr(key_move) - 0x2)
    hex ff ff
    KEY_RIGHT
    eval(adr(key_move) - 0x2)
    hex 01 00
    KEY_1
    eval(adr(key_write) - 0x2)
    hex cc 00
    KEY_0
    eval(adr(key_write) - 0x2)
    hex cd 00
    KEY_SHIFT
    eval(adr(restore) - 0x2)
    hex 00 00
    eval(adr(key_loop) - 0x2)

lbl weights
    hex 64 64 5E 40 5C 84 75 64 00
    hex 64 62 4C 54 63 51 70 64 00
    hex 64 69 4C 82 BB 48 5A 64 00
    hex 64 53 58 8F C8 46 30 64 00
    hex 64 37 43 96 C6 44 38 64 00
    hex 64 51 36 80 99 36 42 64 00
    hex 64 62 2F 4B 67 3F 63 69 00
    hex 64 64 65 40 68 77 7C 6D 00

    hex 00 00

lbl picture
    lbl line_1
        hex CD CD CD CD CD CD CD CD 00
    lbl line_2
        hex CD CD CD CD CD CD CD CD 00
    lbl line_3
        hex CD CD CD CD CD CD CD CD 00
    lbl line_4
        hex CD CD CD CD CD CD CD CD 00
    lbl line_5
        hex CD CD CD CD CD CD CD CD 00
    lbl line_6
        hex CD CD CD CD CD CD CD CD 00
    lbl line_7
        hex CD CD CD CD CD CD CD CD 00
    lbl line_8
        hex CD CD CD CD CD CD CD CD 00

lbl end
    hex 00 00 00 00


@section.launcher at 0xd180
hex FD 24 
0xd72e   # er14
setlr_pc
setsfr
clear()
xr0 = font_size, hex 08 30
[er0]=r2
xr0 = 0xd730, 0xe9e0        # dst, src
call 09451
hex fe 02       # size
sp = er14, pop er14
