org 0xd730 
  setlr 
  setsfr
  di,rt 
  buffer_clear 
print_text_score:
  xr0 = hex 0a 01, adr_of [+4784] text_score
  smallprint
print_player:
  xr0 = hex 58 0f 08 08
  render_bitmap
  er0 = adr_of player_bitmap
print_object_1:
  xr0 = hex b0 01 08 14 
  render_bitmap
  er0 = adr_of object_bitmap
print_object_2:
  xr0 = hex b0 2b 08 14 
  setlr
  render_bitmap
  er0 = adr_of object_bitmap
  render.ddd4
check_key:
  er0 = adr_of key
  getkey 
  pop er0
key:
  0x0000
  ea = adr_of key_table
  call 09C20
  call 1C64A
  sp = er6, pop er8
if_up:
  xr0 = adr_of addr_var_b, var_b 
  calc_func
  setlr
  xr0 = adr_of [+4786] key_table, adr_of [-2] calc_y
  [er0]=er2,rt
  er14 = adr_of [-2] calc_y
  sp=er14, pop er14
ngat_key:
  setlr
  xr0=adr_of [+4786] key_table, adr_of [-2] if_up
  [er0]=er2,rt
calc_y:
  xr0 = adr_of addr_var_b_2, var_b 
  calc_func
  xr0 = adr_of addr_a, var_a 
  calc_func
check_player:
  setlr
  ea = adr_of touch_table
  er2 = adr_of [+4788] print_player
  er0=[er2],r2 = 9,rt
  call 09c20
  call 1c64a
  sp = er6,pop er8
check_cot:
  setlr
  ea = adr_of cot_table
  er2 = adr_of [+4788] print_object_1
  er0=[er2],r2 = 9,rt
  call 09c20
  call 1c64a
  sp = er6,pop er8
setup_score:
  xr0 = adr_of addr_score, var_c 
  calc_func
  goto add_func_score
if_touch_player:
  setlr
  er2 = adr_of [+4788] print_player
  er0=[er2],r2 = 9,rt
  r0 = 0
cmp_func_1:
  er2 = 0x1400
  er0 == er2 || !(r0 < 0x4E || r0 > 0x5F) ? r0 = 1 : r0 = 0 -> rt
  er4 = adr_of [-2] if_touch_cot
  pop er2  
  adr_arith if_touch-adr_arith if_touch_cot
  er0*=r2,er2 = er0,er0+=er4,rt
  er14 = er0,pop xr0
  0x30303030
  sp = er14,pop er14
if_touch_cot:
  setlr
  er2 = adr_of [+4788] print_player 
  er0=[er2],r2 = 9,rt
  r0 = 0
cmp_func_2:
  er2 = 0x2300
  er2 > er0 ? r0 = 0 : r0 = 1 -> rt
  er4 = adr_of [-2] if_not_touch
  er2 = 0x000A
  er0*=r2,er2 = er0,er0+=er4,rt
  er14 = er0,pop xr0
  0x30303030
  sp = er14,pop er14
if_not_touch:
  goto add_func_score
if_touch:
  xr0 = hex 13 d1 01 00 
  [er0]=r2
  xr0 = adr_of add_27, var_a 
  calc_func
  xr0 = var_c, hex 00 00
  num_fromdigit
  xr0 = adr_of reset, var_b 
  calc_func
  buffer_clear
  xr0 = 0x010e, adr_of text_over
  smallprint
  xr0 = 0x110e, adr_of text_score
  smallprint
  xr0 = 0x210e,adr_of text_shift
  smallprint
  xr0 = 0x310e, adr_of text_dev
  smallprint
  render.ddd4
  waitshift
if_touch_cot_fail:
  xr0 = adr_of addr_random, 0xe500
  calc_func
  er0 = 0xe500
  num_to_byte
  er2 = adr_of [+4791] print_object_1
  [er2]=r0, r2=0
  er2 = adr_of [+4789] cmp_func_1
  [er2]=r0,r2 = 0
  setlr
  r1 = 0,rt
  er2 = 0x000e 
  er0+=er2,rt
  er2 = adr_of [+4789] cmp_func_2
  [er2]=r0,r2 = 0
  er2 = 0x0008
  er0+=er2,rt
  er2 = adr_of [+4789] print_object_2
  [er2]=r0,r2 = 0
  er2 = er0,er0+=er4,rt
  er0 = 0x003f
  er0-=er2,rt
  er2 = adr_of [+4791] print_object_2
  [er2]=r0,r2 = 0
  er0 = 0x00b0
  er2 = adr_of [+4788] print_object_1
  [er2]=r0,r2=0
  er2 = adr_of [+4788] print_object_2
  [er2]=r0,r2=0
add_func_score:
  xr0 = var_c , adr_of [+4790] text_score
  num_to_str
  setlr
  er0 = var_a 
  num_to_byte
  er2 = adr_of [+4789] print_player
  [er2]=r0,r2 = 0
check_move_left:
  er2 = 0xffff 
  er8 = adr_of [+4788] print_object_1
  [er8]+=er2, pop xr8
  adr_of [+4788] print_object_2
  0x3030
  er2 = 0xffff
  [er8]+=er2, pop xr8
  0x30303030
loop:
  xr0 = 0xd184d630
  BL strcpy
  er14 = 0xd62e
  sp = er14,pop er14
key_table:
  hex 80 04 
  adr_of [-2] if_up
  hex 00 00 
  adr_of [-2] ngat_key
touch_table:
  hex 58 02 
  adr_of [-2] if_touch
  hex 58 38 
  adr_of [-2] if_touch
  hex 00 00 
  adr_of [-2] check_cot
cot_table:
  0x0101   
  adr_of [-2] if_touch_cot_fail
  0x0160
  adr_of [-2] if_touch_player
  0x015e
  adr_of [-2] if_touch_player
  0x015c
  adr_of [-2] if_touch_player
  0x015a
  adr_of [-2] if_touch_player
  0x0148
  adr_of [-2] setup_score
  0x0000
  adr_of [-2] add_func_score
addr_var_b:
  adr_of b
addr_var_b_2:
  adr_of b2 
addr_a:
  adr_of a
addr_random:
  adr_of random
addr_score:
  adr_of score
reset:
  adr_of restart 
add_27:
  adr_of from27
b:
  hex a7 31 2e 38 00 00
b2:
  hex 43 a6 30 2e 30 39 00 00
a:
  hex 42 a6 43 00
restart:
  hex 30 00
from27:
  hex 32 37 00 00
score:
  hex 44 a6 31 00
random:
  hex 87 31 30 2c 33 31 D0 00
player_bitmap:
  hex 3c 7e ff ff ff ff 7e 3c 
text_over:
  str"Game~Over"
  0x00
text_shift:
  str"Shift~to~restart~"
  0x00
text_dev:
  str"Dev:~MinhCasiok12"
  0x00
text_score:
  str"Score:0"
  hex 00 00 00 00 00
object_bitmap:
  hex ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff

