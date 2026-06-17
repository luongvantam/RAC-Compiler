func mai(h) {
    return eval(adr(h) - 0x2)
}

org 0xd730
lbl main
er0 = mai(main)
