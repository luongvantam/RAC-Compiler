/*
    8×8 Single-Neuron Neural Network for fx580vnx
    * Binary Digit Classifier (0 vs 1)
    * Accuracy: ~70–85%
    * Created by luongvantam
    * Use https://github.com/luongvantam/RAC-Compiler/ to compile this program.
*/

@build {
    output.file = true
    output.file_name = "output.txt"
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
    xr0 = eval(adr(var_i) + dist.main), 0xd0f5
    [er2]=r0,r2=0
    [er0]=r2
    xr0 = 0xd324, 0xdc90
    BL memcpy,pop er0
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
    xr12 = eval(adr(table_key) - 0xa), eval(adr(table_key) - 0xa)
    call 17B40
    pop er0
    lbl key
        hex 00 00
    ea_switchcase
    er6 = [ea+]
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
    goto jump_to_start

lbl var_i
    hex 00 00

lbl main
    setlr_pc
    clear()
    qr0 = 0x3d, 0x1b, eval(adr(text_loading) + dist.main), hex 00 00 00 00
    call 0828C
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
    var_c; hex 00 00
    sp = er14, pop er14
    lbl addr_jump_to_restore_in_add_i
        eval(adr(restore) - 0x2)

lbl add_i
    er8 = eval(adr(var_i) + dist.main - 5)
    [er8+5]+=1,pop er8
    adr(addr_jump_to_restore_in_add_i, dist.main)
    sp = [er8], pop er8

lbl print_result
    /*
        if y > threshold:
            r0 = 0
        else:
            r0 = 1
    */
    num_to_hex
    setlr_pc
    er2 = er0, er0 += er4, rt
    er0 = var_d
    num_to_hex
    setlr_pc
    er0 - er2_gt,r0 = 0|r0 = 1,rt
    clear()
    r1=0,rt
    er2 = adr(table_text)
    load_table
    er14 = er0, pop xr0
    hex 11 11
    adr(text_one)
    sp = er14,pop er14

lbl table_text
    eval(adr(if_num_is_one) - 0x2)
    eval(adr(if_num_is_zero) - 0x2)

lbl if_num_is_one
    er8 = adr(if_num_is_zero, -5)
    [er8+5]+=1,pop er8
    hex 00 00

lbl if_num_is_zero
    call 222B3      # er2 += 4, bl line_print.col_0

lbl print_output
    xr0 = 0x0101, eval(adr(tilte) + dist.main)
    call 222B4
    xr0 = 0x0909, eval(adr(text) + dist.main)
    call 222B4
    xr0 = 0x3939, eval(adr(text_cre) + dist.main)
    call 222B4
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
    hex cc 87
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
call 0875D
hex fe 02       # size
sp = er14, pop er14
