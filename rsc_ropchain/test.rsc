@section.main at 0xd730
setlr_pc
er8 = hex 21 21
pop xr0
hex 00 d4
hex 00 d4
call 23DBC
hex 00 00 00 00 00 00 00 00 00 00 00 00
brk

@section.launcher at 0xd180
hex fd 24
0xd72e
sp = er14, pop er14

@section.text at 0xd400
"hello"
hex 00
