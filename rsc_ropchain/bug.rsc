@section.main at 0xd730

pop lr
xr0 = 0xd400, 0x0000
call 24672
hex 01 00 00 00

@section.launcher at 0xd180

hex fd 24 2e d7
sp = er14, pop er14