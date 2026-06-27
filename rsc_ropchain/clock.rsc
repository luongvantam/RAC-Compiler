# coded by @.minh12312
org 0xe9e0

lbl rtc
    er0=0xF0C0
    r0=[er0]
    hex_byte
    er4=adr(seconds)
    [er4]=er0,pop er0,rt
    0xF0C1                  # er0 = 0xF0C1
    r0=[er0]
    hex_byte
    er4=adr(minutes)
    [er4]=er0,pop er0,rt
    0xF0C2                  # er0 = 0xF0C2
    r0=[er0]
    hex_byte
    er4=adr(hours)
    [er4]=er0,pop er0,rt
    0x3021                  # er0 = 0x3021

lbl spell
    er2=adr(clock)
    printline
    render.ddd4

lbl loop
    qr0 = hex 30 d6 98 d1 30 30 2e d6
    BL strcpy
    sp=er6, pop er8

lbl clock
    lbl hours
        hex 20 20
    hex 3A 01
    lbl minutes
        hex 20 20
    hex 3A 01
    lbl seconds
        hex 20 20
hex 00 00
