@section.main at 0xd730 backup 0xe9e0

home:
  setlr_pc
  setsfr
  buffer_clear
random_pos_x:
  xr0 = adr_of random_pos, var_a
  calc_func
  pop xr0
  pos:
    hex 00 37 08 08
  render_bitmap
  xr0 = adr_of bot, 0x0000
  render.ddd4
  er0 = var_a
  num_to_hex
  er2 = adr_of [+4784] pos
  [er2] = r0,r0 = 0
loop:
  er0 = hex 00 05
  delay
  er14 = 0xd178
  call 27738
random_pos:
  adr_of random
random:
  hex 87 31 2c 31 38 34 d0 00    # RanInt(1,184)
bot:
  hex ff ff ff ff ff ff ff ff
hex 00 00 00 00

@section.launcher at 0xd180
hex fd24 24 d7 34 7b 31 30 30 d7 e0 e9 7e e5 31 30 fe 01

