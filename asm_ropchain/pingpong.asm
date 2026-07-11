org 0xd730

start:
    setlr 
    setsfr 
    di,rt 
    buffer_clear

noflash:
    xr0 = hex 13 d1 01 00 
    [er0]=r2 

key_proccessing:
    er0 = adr_of key
    getkey
    setlr_pc
    ea = adr_of move_table
    pop er0
    key:
        0x0000
    cmp_ea

moving_pad:
    qr0=[ea],lea D002H,[ea]=qr0
    er2 = er0,er0 = er2,pop er8,rt
    adr_of [+4788] print_pad 
    [er8]+=er2,pop xr8
    0x00000000

check_pad_range:
    er2 = adr_of [+4788] print_pad
    er0 = [er2],r2 = 9,rt
    ea = adr_of litmit_table
    cmp_ea
    qr0 = [ea],lea D002H,[ea]=qr0
    [er0]=er2,rt

print_line_draw_and_setup_score:
    xr0 = hex b7 01 b7 32
    line_draw
    xr0 = hex 08 32 08 01
    line_draw
    xr0 = hex 08 32 b7 32
    line_draw
    xr0 = 0xd32e, adr_of [+4790] text_score
    num_to_str
    er0 = 0x0000
    xr0 = 0x370a, adr_of [+4784] text_score
    smallprint

print_pad:
    xr0 = hex 60 33 0a 03
    render_bitmap
    er0 = adr_of pad 

print_ball:
    xr0 = hex 60 10 08 08 
    er8 = er0
    render_bitmap
    er0 = adr_of ball 
    render.ddd4

check_ball_range_x:
    setlr_pc
    er0 = er8
    r1 = 1
    ea = adr_of x_table
    cmp_ea
    qr0=[ea],lea D002H,[ea]=qr0
    [er0]=er2,rt

check_ball_range_y:
    er0 = er8
    r0 = 0
    ea = adr_of y_table
    cmp_ea
    qr0=[ea],lea D002H,[ea]=qr0
    [er0]=er2,rt

ball_table_x:
    er2 = 0x0001
    er8 = adr_of [+4788] print_ball
    [er8]+=er2, pop xr8
    adr_of [+4788] print_ball
    0x0000

ball_table_y:
    er2 = 0x0100
    [er8]+=er2, pop xr8
    0x00000000

check_ball_y:
    er2 = adr_of [+4789] print_ball
    r0 = [er2]
    r1 = 0,rt
    ea = adr_of y_table_pad 
    cmp_ea
    er6 = [ea+]
    sp = er6, pop er8

check_pad_and_ball:
    er0 = adr_of [+4788] print_pad
    r0 = [er0]
    r1 = 0,rt
    er2 = er0, er0+=er4,rt
    er0 = adr_of [+4788] print_ball
    r0 = [er0]
    r1 = 0,rt
    er0-=er2,rt
    r1 = 1
    ea = adr_of a_table
    cmp_ea
    er6 = [ea+]
    sp = er6, pop er8

if_touch_player:
    xr0 = adr_of addr_point_calc, 0xd32e
    calc_func
    xr0 = adr_of [+4788] ball_table_y, 0xff00
    [er0]=er2,rt
    goto loop

if_lose:
    buffer_clear
    xr0 = 0xd32e, 0x000a
    memzero
    setlr_pc
    xr0 = adr_of [+4788] print_ball, hex 10 10
    [er0]=er2,rt
    xr0 = adr_of [+4788] print_pad, hex 50 33
    [er0]=er2,rt
    xr0 = adr_of [+4788] ball_table_x, 0x0001
    [er0]=er2,rt
    xr0 = adr_of [+4788] ball_table_y, 0x0100
    [er0]=er2,rt
    xr0 = 0x010a, adr_of text_lose 
    smallprint
    xr0 = 0x110a, adr_of text_shift 
    smallprint 
    xr0 = 0x210a, adr_of test_dev 
    smallprint
    xr0 = 0x310a, adr_of text_score
    smallprint
    render.ddd4 
    waitshift

loop:
    er0 = 0x0100
    delay 
    qr0 = 0xd62e3030d184d630
    call 203c8
    call 21f74

addr_point_calc:
    adr_of point_calc

point_calc:
    hex 42 a6 31 00

pad:
    hex ff ff ff ff ff ff  

ball:
    hex 3c 7e ff ff ff ff 7e 3c

move_table:
    hex 40 04
    hex fe ff 
    hex 80 08
    hex 02 00
    hex 00 00
    hex 00 00

x_table:
    hex 0a 01
    adr_of [+4788] ball_table_x
    0x0001
    hex ae 01
    adr_of [+4788] ball_table_x
    0xffff
    hex 00 00
    0x00000000

y_table:
    hex 00 02
    adr_of [+4788] ball_table_y
    0x0100
    hex 00 00
    0x00000000

y_table_pad:
    hex 2a 00
    adr_of [-2] check_pad_and_ball
    hex 00 00
    adr_of [-2] loop

a_table:
    hex f8 01
    adr_of [-2] if_touch_player
    hex f9 01
    adr_of [-2] if_touch_player
    hex fa 01
    adr_of [-2] if_touch_player
    hex fb 01
    adr_of [-2] if_touch_player
    hex fc 01
    adr_of [-2] if_touch_player
    hex fd 01
    adr_of [-2] if_touch_player
    hex fe 01
    adr_of [-2] if_touch_player
    hex ff 01
    adr_of [-2] if_touch_player
    hex 00 01
    adr_of [-2] if_touch_player
    hex 01 01
    adr_of [-2] if_touch_player
    hex 02 01
    adr_of [-2] if_touch_player
    hex 03 01
    adr_of [-2] if_touch_player
    hex 04 01
    adr_of [-2] if_touch_player
    hex 05 01
    adr_of [-2] if_touch_player
    hex 06 01
    adr_of [-2] if_touch_player
    hex 07 01
    adr_of [-2] if_touch_player
    hex 08 01
    adr_of [-2] if_touch_player
    hex 00 00
    adr_of [-2] if_lose 

litmit_table:
    hex b8 33
    adr_of [+4788] print_pad 
    0x33b6
    hex fe 32
    adr_of [+4788] print_pad
    0x3300

text_lose:
    str"Game~Over"
    0x00

text_shift:
    str"Shift~to~restart"
    0x00

test_dev:
    str"Origi:@dusaothi~Dev:@Black"
    0x00

text_score:
    str"Score:0"
    0x00