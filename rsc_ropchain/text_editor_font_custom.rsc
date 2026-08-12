/*
Text editor with custom font for fx580vnx

* Character range: 94 characters (0x20-0x7E)
* Font size: 7x7 pixels
* Original code size (without font data): 336 bytes
* Font data: 7 bytes/character
* Created by luongvantam
*/

@section.main at 0xd730 backup 0xe9d4

lbl get_key
    getkeycode
    setlr_pc
    er8 = er0
    r0 >> 4,rt
    r1|=r0,rt
    ea = adr(table_key)
    ea_switchcase
    er0 = er8
    er6 = [ea+]
    hex 75 1f 02 00

    eval(adr(position) + dist.main)
lbl delete
    pop qr0
    hex 00 00
    hex F8 FF
    hex 00 00
    adr(get_font, -2)
    [er8]+=er2, pop xr8
    adr(update_pos); hex 00 00
    [er8] = r0
    sp = er6, pop er8

    eval(adr(position) + dist.main - 8)
lbl clear
    r0 = 1
    call 0E5BE
    adr(jump_to_clear)
    sp = [er8], pop er8

    eval(adr(pointer) + dist.main - 5)
lbl process_type_key
    pop er2
    lbl pointer
        0xd090
    [er2]=r0,r2=0
    [er8+5]+=1,pop er8
    adr(pointer)
    r0 = [er8],r1 = 0,er2 = er0,er0 = er2,pop er8,rt
    hex 00 00
    ea = adr(table_key)
    ea_switchcase
    er6 = [ea+]
    hex 74 1f           # sp=er6,pop er8

lbl check_font
    call 130A2
    eval(0xd090 - 0xf1e)
    adr(table_jump)
    hex 20 FF 00 00
    er0 = [er0 + 3870]
    call 20840
    r0 = r1,rt
    er8 = er0
    call 1428C
    call 1E60A
    # 1428C + 1E60A thành r0-0_ne,er0=0|er0=1,rt
    load_table
    er14 = er0, pop xr0
    eval(adr(pointer) + dist.main); hex 90 00
    [er0]=r2
    call 0A910

lbl get_font
    er0 = er8
    r2 = r0, pop er0
    hex 07 00
    er0 *= r2,er2 = er0,er0 += er4,rt
    er2 = er0,er0 += er4,rt
    er8 = adr(addr_bitmap)
    [er8]+=er2, pop xr8
    eval(adr(position) + dist.main)
    lbl jump_to_clear
        adr(jump_to_render_ok, -2)

lbl check_line
    er0 = er8
    r0=[er0]
    ea = adr(table_key)
    ea_switchcase
    qr0=[ea]
    er8 = er0
    [er8]+=er2,pop xr8
    lbl table_jump
        adr(get_font, -2)
        adr(render, -2)

lbl render
    pop xr0
    eval(adr(position) + dist.main)
    hex 07 07
    er0 = [er0],pop xr8,rt
    lbl position
        hex 01 01
    hex 00 00
    render_bitmap
    pop er0, pop er8
    lbl addr_bitmap
        eval(adr(font) + dist.main)
    eval(adr(position) + dist.main)

lbl continue
    pop er2
    lbl update_pos
        hex 08 00
    [er8]+=er2, pop xr8
    lbl jump_to_render_ok
        buffer_clear

lbl restore
    render.ddd4
    er14 = adr(launcher, +2)
    hex 38 77           # call 27738

lbl table_key
    hex 02 fe
    adr(clear, -2)
    hex 03 03
    adr(process_type_key, -2)
    hex 03 ff
    adr(delete, -2)

    hex 91 00
    adr(check_font, -2)

    hex F9
    adr(table_key)[1]
    eval(adr(position) + dist.main); hex B8 F8
    hex B9
    adr(table_key)[1]
    eval(adr(position) + dist.main); hex 48 07
    
    hex 00 00
    adr(restore, -2)

lbl font
    hex 00 00 00 00 00 00 00    # U+0020 (space)
    hex 18 3C 3C 18 18 00 18    # U+0021 (!)
    hex 6C 6C 00 00 00 00 00    # U+0022 (")
    hex 6C 6C FE 6C FE 6C 6C    # U+0023 (#)
    hex 30 7C C0 78 0C F8 30    # U+0024 ($)
    hex 00 C6 CC 18 30 66 C6    # U+0025 (%)
    hex 38 6C 38 76 DC CC 76    # U+0026 (&)
    hex 60 60 C0 00 00 00 00    # U+0027 (')
    hex 18 30 60 60 60 30 18    # U+0028 (()
    hex 60 30 18 18 18 30 60    # U+0029 ())
    hex 00 66 3C FF 3C 66 00    # U+002A (*)
    hex 00 30 30 FC 30 30 00    # U+002B (+)
    hex 00 00 00 00 30 30 60    # U+002C (,)
    hex 00 00 00 FC 00 00 00    # U+002D (-)
    hex 00 00 00 00 00 30 30    # U+002E (.)
    hex 06 0C 18 30 60 C0 80    # U+002F (/)
    hex 7C C6 CE DE F6 E6 7C    # U+0030 (0)
    hex 30 70 30 30 30 30 FC    # U+0031 (1)
    hex 78 CC 0C 38 60 CC FC    # U+0032 (2)
    hex 78 CC 0C 38 0C CC 78    # U+0033 (3)
    hex 1C 3C 6C CC FE 0C 1E    # U+0034 (4)
    hex FC C0 F8 0C 0C CC 78    # U+0035 (5)
    hex 38 60 C0 F8 CC CC 78    # U+0036 (6)
    hex FC CC 0C 18 30 30 30    # U+0037 (7)
    hex 78 CC CC 78 CC CC 78    # U+0038 (8)
    hex 78 CC CC 7C 0C 18 70    # U+0039 (9)
    hex 00 30 30 00 00 30 30    # U+003A (:)
    hex 00 30 30 00 30 30 60    # U+003B (;)
    hex 18 30 60 C0 60 30 18    # U+003C (<)
    hex 00 00 FC 00 00 FC 00    # U+003D (=)
    hex 60 30 18 0C 18 30 60    # U+003E (>)
    hex 78 CC 0C 18 30 00 30    # U+003F (?)
    hex 7C C6 DE DE DE C0 78    # U+0040 (@)
    hex 30 78 CC CC FC CC CC    # U+0041 (A)
    hex FC 66 66 7C 66 66 FC    # U+0042 (B)
    hex 3C 66 C0 C0 C0 66 3C    # U+0043 (C)
    hex F8 6C 66 66 66 6C F8    # U+0044 (D)
    hex FE 62 68 78 68 62 FE    # U+0045 (E)
    hex FE 62 68 78 68 60 F0    # U+0046 (F)
    hex 3C 66 C0 C0 CE 66 3E    # U+0047 (G)
    hex CC CC CC FC CC CC CC    # U+0048 (H)
    hex 78 30 30 30 30 30 78    # U+0049 (I)
    hex 1E 0C 0C 0C CC CC 78    # U+004A (J)
    hex E6 66 6C 78 6C 66 E6    # U+004B (K)
    hex F0 60 60 60 62 66 FE    # U+004C (L)
    hex C6 EE FE FE D6 C6 C6    # U+004D (M)
    hex C6 E6 F6 DE CE C6 C6    # U+004E (N)
    hex 38 6C C6 C6 C6 6C 38    # U+004F (O)
    hex FC 66 66 7C 60 60 F0    # U+0050 (P)
    hex 78 CC CC CC DC 78 1C    # U+0051 (Q)
    hex FC 66 66 7C 6C 66 E6    # U+0052 (R)
    hex 78 CC E0 70 1C CC 78    # U+0053 (S)
    hex FC B4 30 30 30 30 78    # U+0054 (T)
    hex CC CC CC CC CC CC FC    # U+0055 (U)
    hex CC CC CC CC CC 78 30    # U+0056 (V)
    hex C6 C6 C6 D6 FE EE C6    # U+0057 (W)
    hex C6 C6 6C 38 38 6C C6    # U+0058 (X)
    hex CC CC CC 78 30 30 78    # U+0059 (Y)
    hex FE C6 8C 18 32 66 FE    # U+005A (Z)
    hex 78 60 60 60 60 60 78    # U+005B ([)
    hex C0 60 30 18 0C 06 02    # U+005C (\)
    hex 78 18 18 18 18 18 78    # U+005D (])
    hex 10 38 6C C6 00 00 00    # U+005E (^)
    hex 00 00 00 00 00 00 FF    # U+005F (_)
    hex 30 30 18 00 00 00 00    # U+0060 (`)
    hex 00 00 78 0C 7C CC 76    # U+0061 (a)
    hex E0 60 60 7C 66 66 DC    # U+0062 (b)
    hex 00 00 78 CC C0 CC 78    # U+0063 (c)
    hex 1C 0C 0C 7C CC CC 76    # U+0064 (d)
    hex 00 00 78 CC FC C0 78    # U+0065 (e)
    hex 38 6C 60 F0 60 60 F0    # U+0066 (f)
    hex 00 76 CC CC 7C 0C F8    # U+0067 (g)
    hex E0 60 6C 76 66 66 E6    # U+0068 (h)
    hex 30 00 70 30 30 30 78    # U+0069 (i)
    hex 0C 00 0C 0C CC CC 78    # U+006A (j)
    hex E0 60 66 6C 78 6C E6    # U+006B (k)
    hex 70 30 30 30 30 30 78    # U+006C (l)
    hex 00 00 CC FE FE D6 C6    # U+006D (m)
    hex 00 00 F8 CC CC CC CC    # U+006E (n)
    hex 00 00 78 CC CC CC 78    # U+006F (o)
    hex 00 DC 66 66 7C 60 F0    # U+0070 (p)
    hex 00 76 CC CC 7C 0C 1E    # U+0071 (q)
    hex 00 00 DC 76 66 60 F0    # U+0072 (r)
    hex 00 00 7C C0 78 0C F8    # U+0073 (s)
    hex 10 30 7C 30 30 34 18    # U+0074 (t)
    hex 00 00 CC CC CC CC 76    # U+0075 (u)
    hex 00 00 CC CC CC 78 30    # U+0076 (v)
    hex 00 00 C6 D6 FE FE 6C    # U+0077 (w)
    hex 00 00 C6 6C 38 6C C6    # U+0078 (x)
    hex 00 CC CC CC 7C 0C F8    # U+0079 (y)
    hex 00 00 FC 98 30 64 FC    # U+007A (z)

@section.launcher at 0xd180
lbl launcher
hex fd 20
0xd730
hex fe 01
hex 30 30 30 30
0xe9d4
0xd724
setlr_pc
setsfr
xr0 = 0xd0f5, hex 30 30
[er0]=r2
hex 34 7b 31 fe 02 30 11 d1
[er2]=r0,r2=0
memcpy_auto_jump
