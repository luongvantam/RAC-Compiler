# Source: Nguyen Minh Khang, edited by @luongvantam
@section.main at 0xd730 backup 0xe9e0

def buffer_to_input : 0x27738

lbl program
    lbl print
        xr0 = hex 00 01 08 08
        render_bitmap
        er0 = adr(bitmap)
        render.ddd4
        
        lbl process_key
        getkeycode
        ea = adr(table)
        ea_switchcase
        call 0x1a7c0
        er8 = adr(print, 4788)
        [er8]+=er2,pop xr8
        hex 00 00 00 00

    lbl loop
        er14 = adr(save_register, 2)
        buffer_to_input

lbl table
    hex 1c fc
    0xf800
    hex 1d fc
    0x0800
    hex 1e fc
    0x0008
    hex 1f fc
    0xfff8
    hex 00 00
    0x0000

lbl bitmap
    hex ff ff ff ff ff ff ff ff

@section.launcher at 0xd180
lbl save_register
    0xfd20
    adr(program)
    hex fe 01
    hex 30 30 30 30
    adr(program, 4784)
    adr(program, -12)

lbl launch
    setlr_pc
    setsfr
    buffer_clear
    xr0 = 0xd0f5, hex 30 30
    [er0]=r2
    memcpy_auto_jump