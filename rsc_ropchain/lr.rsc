@section.main at 0xd730

pop lr
[er0] = r2
qr0,rt = 0xd400, hex 01 00 00 00 00 00
qr0,rt = 0xd402, hex 02 00 00 00 00 00
qr0,rt = 0xd404, hex 03 00 00 00 00 00
nop
brk

@section.launcher at 0xd180
hex fd 24
0xd72e
sp = er14, pop er14