@section.main at 0xe9e0

setlr_pc
setsfr
getkeycode
er4 = 0xd400
[er4] = er0, pop er0, rt
hex 30 30
brk

@section.launhcer at 0xd180
hex fd 24
0xe9de
sp = er14, pop er14

