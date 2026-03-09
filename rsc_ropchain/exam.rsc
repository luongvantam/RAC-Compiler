# This is an exam code.

@set.main
org 0xd730
# backup at 0xe9e0

var person = "Bob"

func print4line(x, y, addr) {
    xr0 = x, y, addr
    line_print
    er0 = x, eval(y+0x10)
    line_print
    er0 = x, eval(y+0x20)
    line_print
    er0 = x, eval(y+0x30)
    line_print
    render()
}

lbl main
    setlr
    setsfr
    clear()
    print4line(0x01, 0x01, adr(text))

lbl jump
    goto idk

lbl restore
    di,rt
    clear()
    xr0 = adr(length), hex 01 00
    [er0] = er2,rt
    qr0 = pr_length, 0xe9e0, 0xd730, eval(adr(main) - 0x2)
    0x8932

lbl length
    eval(adr(end) - adr(length))
    0x0000
    sp = er6, pop er8

loop 4 {
    hex 00 00
}

lbl idk
    delay(0x0101)
    goto restore

lbl text
    "Hello {person}"
    hex 00

lbl end
    hex 00 00

@set.launcher
org 0xd180
mode_fd24
setlr
setsfr
xr0 = hex 30 d7 e0 e9
call 09451
hex fe 02
er14 = hex 2e d7
sp=er14,pop er14