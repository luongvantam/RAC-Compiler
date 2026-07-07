@section.main at 0xd730 backup 0xe9e0

lbl main
    setlr
    setsfr
    buffer_clear.ca54
    smallprint(0x8,0x1,eval(adr(line_1)+dist.main))
    render()
lbl line_1
    "Hello World"
    hex 00 00

hex 00 00 00 00

@section.launcher at 0x9268
hex FD 26 30 30 36 81 31 30 30 C0 30 30 E3 30 2E C0 10 8F 31 30 0C 01 30 30 44 13 32 30