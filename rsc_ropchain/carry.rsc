@section.main at 0xd730
setlr_pc
er0 = hex ff 00
r0 += 1,rt
call 09AE8
brk

@section.launcher at 0xd180
hex fd 24
hex 2e d7
sp = er14, pop er14
