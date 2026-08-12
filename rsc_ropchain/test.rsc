@section.main at 0xd730
setlr_pc
setsfr
buffer_clear

xr0 = hex 00 01 00 d4
line_print
er0 = hex 00 10
line_print
er0 = hex 00 20
line_print
render.ddd4

brk

@section.launcher at 0xd180
hex fd 24 2e d7
sp = er14, pop er14

@section.text at 0xd400
hex 30 30 30 30 30 30 30 30 30 30 30 30 30 30 30 30
hex 31 31 31 31 31 31 31 31 31 31 31 31 31 31 31 31
hex 32 32 32 32 32 32 32 32 32 32 32 32 32 32 32 32
hex 33 33 33 33 33 33 33 33 33 33 33 33 33 33 33 33
