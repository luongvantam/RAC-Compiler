def string_to_byte : 20840
def smart_printline : 099c6
def set_small_font : 2f204

@section.main at 0xdde0 backup 0xdf60

lbl program
    lbl display
        pop er0, pop er8
            eval(adr(address) + dist.main + 5)
            eval(adr(address) + dist.main + 4)
        r0 = [er0]
        hex_byte
        er2 = er0,er0+=er4,rt
        er0 = er8
        r0 = [er0]
        hex_byte
        ea = eval(adr(address_text) + dist.main + 6)
        [ea+]=er2, [ea+]=er0,rt
        pop er4, pop er2, pop er8, er0=er2,rt
            eval(adr(value_text) + dist.main + 6)
            eval(adr(address) + dist.main + 4)
            adr(keycode, +4)
        er0 = [er2], r2 = 9,rt
        r0 = [er0]
        hex_byte
        [er4]=er0,pop er0,rt
            eval(adr(address_text) + dist.main)
        r2 = 3,rt
        smart_printline

    lbl process_val_key
        er0 = er8
        getkey
        ea = adr(val_table)

            lbl keycode
                pop er0, pop er8
                    hex 00 00
                    eval(adr(address) + dist.main + 4)

        ea_switchcase
        qr0 = [ea],lea D002H,[ea]= qr0
        [er8]+=er2,pop xr8
            0xf00a
            adr(keycode, +4)
        [er8]=r0
        sp = er4,sp+=32h,pop xr4,pop qr8

    lbl set_sp
        set_small_font
        er8 = adr(address, +4)
        sp = [er8],pop er8

    lbl check_func_key
        xr0 = adr(keycode, +4), 0x83da
        cvt_keycode
        er8 = er0
        r0 >> 4,rt
        r1|=r0,rt
        er2 = eval(adr(func_table) +dist.main)
        [er2]=r0,r2=0
        ea = adr(func_table)
        ea_switchcase
        er0 = er8
        er6 = [ea+]
        sp = er6,pop er8

            lbl process_type_key
                eval(adr(pointer) + dist.main + 4 - 5)
                
                    lbl pointer
                        er2 = 0xd150

                [er2]=r0,r2=0
                [er8+5]+=1,pop er8
                    adr(pointer, +4)
                r0 = [er8],r1 = 0,er2 = er0,er0 = er2,pop er8,rt
                    hex 00 00
                ea = adr(type_table)
                ea_switchcase
                er6 = [ea+]
                sp = er6,pop er8

                    lbl inject
                        eval(adr(address) + dist.main + 4 - 5)
                        [er8+5]+=1,pop er8
                            0xc232
                        er0 = er8
                        er0 = [er0 + 3870]
                        string_to_byte
                        r0 = r1,rt
                        
                            lbl address
                                er2 = 0xd550

                        [er2]=r0,r2 = 0
                        xr0 = eval(adr(pointer) + dist.main - 1), 0x0050
                        [er0]=r2
        
    lbl loop
        pop xr4, pop xr12
            pr_org()
            sizeof()
            pr_backup()
            eval(adr(program) - 0xc)
        memcpy_auto_jump

lbl val_table
    hex 40 04 30 00 ff ff
    eval(adr(check_func_key) - 62)

    hex 80 08 30 00 01 00
    eval(adr(check_func_key) - 62)

    hex 40 08 30 00 00 01
    eval(adr(check_func_key) - 62)

    hex 80 04 30 00 00 ff
    eval(adr(check_func_key) - 62)

    hex 04 10 01 00 01 00
    eval(adr(set_sp) - 62)

    hex 00 00 00 00 00 00
    eval(adr(check_func_key) - 62)

lbl func_table
    hex 30 03
    eval(adr(loop) - 2)
    hex 03 03
    adr(process_type_key)

lbl type_table
    hex 51 00
    adr(inject)
    hex 00 00
    adr(loop, -2)

lbl address_text
    "Addr :D550"
    0x0000

lbl value_text
    "Value:00"
    0x0000


@section.launcher at 0xd180
hex FD 24
hex 30 30
xr0 = pr_org(main), 0xe9e0
BL memcpy,pop er0,pop er4
    0x01fe
    hex 30 30
xr0 = pr_backup(main), 0xe9e0
BL memcpy,pop er0,pop er4
    0x01fe
    adr(program, -62)
setlr_pc
di,rt
sp = er4,sp+=32h,pop xr4,pop qr8
