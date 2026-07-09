@section.main at 0xd730

setlr_pc
xr4 = hex 11 22 33 44
call 0AC30              # enter
er2 = 0,er4 = 0,er6 = 0,er8 = 1,rt
call 0AC38              # leave
brk
# output xr4 vẫn là 11 22 33 44

@section.launcher at 0xd180
hex fd 24
0xd72e
sp = er14, pop er14