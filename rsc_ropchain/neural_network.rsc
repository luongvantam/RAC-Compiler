/*
    8×8 Single-Neuron Neural Network for fx580vnx
    * Binary Digit Classifier (0 vs 1)
    * Accuracy: ~70–85%
    * Created by luongvantam
    * Use https://github.com/luongvantam/RAC-Compiler/ to compile this program.
*/

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
    xr0 = eval(adr(var_i) + dist.main), 0xd0f5
    [er2]=r0,r2=0
    [er0]=r2
    xr0 = 0xd324, 0xdc90
    call 09451
    hex 46 00

lbl draw_picture
    xr0 = 0x44,0x01,eval(adr(line_1)+dist.main)
    line_print
    xr0 = 0x44,0x09,eval(adr(line_2)+dist.main)
    line_print
    xr0 = 0x44,0x11,eval(adr(line_3)+dist.main)
    line_print
    xr0 = 0x44,0x19,eval(adr(line_4)+dist.main)
    line_print
    xr0 = 0x44,0x21,eval(adr(line_5)+dist.main)
    line_print
    xr0 = 0x44,0x29,eval(adr(line_6)+dist.main)
    line_print
    xr0 = 0x44,0x31,eval(adr(line_7)+dist.main)
    line_print
    xr0 = 0x44,0x39,eval(adr(line_8)+dist.main)
    line_print
    render()

lbl get_key
    er0 = adr(key)
    getscancode
    setlr_pc
    ea = adr(table_key)
    pop er0
    lbl key
        hex 00 00
    call 09C20
    call 1C64A
    er0 = er8
    er2=er0,er0+=er4,rt
    sp = er6, pop er8
    eval(adr(cursor) + dist.main)

lbl key_move
    [er8]+=er2,pop xr8
    lbl jump_in_key_move
        adr(jump_to_start_in_key)
    lbl jump_to_start_in_key
        eval(adr(jump_to_start) - 0x2)
    sp=[er8],pop er8

lbl key_write
    er0 = eval(adr(cursor) + dist.main)
    er0 = [er0],pop xr8,rt
    lbl jump_in_key_write
        adr(jump_to_start_in_key)
    hex 00 00
    [er0]=r2

lbl key_loop
    sp = [er8], pop er8

lbl weights
    hex 64 64 5E 40 5C 84 75 64 00
    hex 64 62 4C 54 63 51 70 64 00
    hex 64 69 4C 82 BB 48 5A 64 00
    hex 64 53 58 8F C8 46 30 64 00
    hex 64 37 43 96 C6 44 38 64 00
    hex 64 51 36 80 99 36 42 64 00
    hex 64 62 2F 4B 67 3F 63 69 00
    hex 64 64 65 40 68 77 7C 6D 00

lbl var_i
    hex 00 00

lbl main
    setlr_pc
    clear()
    xr0 = 0x3d, 0x1b, eval(adr(text_loading) + dist.main)
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
    r0 = r2
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
    xr0 = eval(adr(var_i) + dist.main), 0x0048
    r0 = [er0]
    r1=0,rt
    er0 - er2_eq,r0 = 1|r0 = 0,rt
    er2 = er0,er0 = er2,pop er8,rt
    adr(if_num_is_zero)
    er0 += er2,rt                               # tương đương er0 += er0 hay er0*=2
    xr12 = adr(table_jump), eval(adr(add_i) - 0x2)
    BL [er12+=r0]     
    var_c; var_d

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
    [er8]+=er2, pop xr8
    hex 00 00 00 00
    xr0 = hex 11 11, adr(text_one)

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
        xr0 = adr(addr_jump_to_main), eval(adr(start) - 12)
        [er0]=er2,rt

lbl add_i
    er4 = eval(adr(var_i) + dist.main)
    [er4] += 1,rt

lbl restore
    di,rt
    pop xr4, pop xr12
    pr_org()
    pr_length
    pr_backup()
    lbl addr_jump_to_main
        adr(main, -12)
    memcpy_auto_jump

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

lbl table_jump
    hex 40 07
    hex 34 7b

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
    adr(jump_to_start_in_key)

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