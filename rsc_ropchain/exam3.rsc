func getkey_er8(addrkey, pad_er4, pad_er6, pad_er8, pad_er10, pad_er12, pad_er14) {
    addrkey
    er14 = adr(leave)
    call 2F5F0
lbl leave
    pad_er4
    pad_er6
    pad_er8
    pad_er10
    pad_er12
    pad_er14
}

distance = eval(0xE630 - 0xE330)
org 0xE330
lbl home
    a = hex 30 30
    a
    b = eval(adr(home) + distance)
    b