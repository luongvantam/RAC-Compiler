# 991cnx ver f
@section.main at 0xd730 backup 0xe9e0

lbl p1main
   DI,RT
   call 086C4           # pop er2, pop er8, er0 = er2, rt

lbl p1pointer
   hex 00 d4
   hex 39 d1
   r0 = [er0]
   call 1D806           # r0 &= 0xf
   [er2] = r0,r2 = 0
   call 2242C
   er2 = er0,er0 += er4,rt
   er0 = er8
   [er0] = r2
   pop er0

lbl p1pos
   eval(adr(p1table) + dist.main)
   er0 = [er0],pop xr8,rt
   eval(adr(p1counter) + dist.main); hex 00 00
   call 0835A           # char_print (r3 = 0)
   render.ddd4
   setlr_pc
   er2 = 1,r0 = r2,rt
   [er8] += er2,pop xr8
   eval(adr(p1pos) + dist.main); hex 00 00
   er2 = hex 02 00
   [er8] += er2,pop xr8
   eval(adr(p1pointer) + dist.main); hex 00 00
   er2 = 1,r0 = r2,rt
   [er8] += er2,pop xr8
   hex 00 00 00 00
   er14 = eval(adr(ac) + 0x12)

lbl p1counter
   call 2110D

lbl p3table
   0xd400
   hex da 61
   0xd4aa
   hex 44 07
   0x0000
   hex 40 07
   qr0 = hex 0d 00, eval(adr(p1counter) + dist.main), adr(key), hex 01 00
   [er2] = r0,r2 = 0
   er2 = 0xd0f5
   [er2] = r0,r0 = 0
   er2 = eval(adr(p1pointer) + dist.main)
   [er2] = r0,r0 = 0
   er0 += er4,rt
   getscancode
   setlr_pc
   setsfr
   pop ea,pop xr4
   adr(p2table)
   hex 00 00

lbl key
   hex 11 45
   er0 = er6,er2 = er12
   ea_switchcase
   xr0 = eval(adr(p1pos) + dist.main), eval(adr(p1table) + dist.main)
   [er0] = er2,rt
   call 1A55A
   hex 38 1d

lbl ac
   hex 02 00
   xr0 = adr(go), adr(p3for)
   [er0] = er2,rt
   xr0 = hex 00 d4, hex 40 00
   memzero
   call 07eec
   setlr_pc
   call 13236
   hex 10 03
   eval(adr(p1main) + dist.main)
   adr(p1main)

lbl go
   eval(adr(p1main) - 0xC)
   er0 = er8
   call 0CD8A
   adr(p3loader)

lbl p2main
   er14 = sp,rt
   call 10744
   call 25366
   hex 00 00
   eval(adr(p3next) - 0x2)

   pop ea,pop xr4
   eval(adr(p3table) + dist.main)

lbl p3counter
   hex 02 00
   hex 00 fb

lbl p3
   pop xr0

lbl p3loader
   hex 11 45
   eval(adr(p3table) + dist.main + 4)
   er8 = [er0],rt
   er0 += er4,rt
   r0 = [er0]
   call 14F02
   call 16CE6
   er4 += er0,r8 = r8,rt
   r0 = [er0]
   [er2] = r0,r0 = 0
   er0 = er4,pop er4
   hex 00 00
   er0 += er8,rt
   er4 += er0,r8 = r8,rt
   r0 = [er0]
   ea_switchcase
   call 19BF0
   xr0 = adr(p3control), hex 00 00
   er2 += er8,rt
   [er0] = er2,rt
   er0 = er10,pop xr8
   adr(p3counterI)
   hex 00 00
   er10 = er0,rt

lbl p3control
   hex ff ff 01 00
   pop er0

lbl nn
   hex 11 00
   call 08D56
   r0 = [er0]
   er8 = er0
   er0 = er4,pop er4
   hex 00 00
   er2 = er0,er0 += er4,rt
   r0 = [er0]
   er0 += er8,rt
   [er2] = r0,r0 = 0
   er0 = er10,pop xr8
   adr(p3counterI)
   hex 00 00
   er2 = er0,er0 += er4,rt
   call 08F18
   [er2] = r0,r0 = 0
   xr0 = eval(adr(p3for) + 0x6), eval(adr(p4) - 0x2)
   [er0] = er2, rt

lbl p3next
   er2 = 1,r0 = r2,rt
   er14 = hex 42 d8
   [er8] += er2,pop xr8
   adr(p3counter)
   hex 00 00
   er2 = 1,r0 = r2,rt
   [er8] += er2,pop xr8

lbl p4base
   eval(adr(p4) - 0x2)
   eval(adr(p4write) - 0x2)

lbl p3counterI
   call 21110

lbl p3return
   adr(p3for)
   hex 86 9a
   eval(adr(ADDR_D940) + dist.main)
   [er8] += er2,pop xr8
   adr(nn)
   hex 36 1d
   call 1DA92
   eval(adr(p3) - 0xe)
   hex 20 00
   [er8] += er2,pop xr8
   hex 00 00
   lbl ADDR_D940
   adr(p3return)
   er14 = er0,pop xr0
   hex 02 00
   adr(p3counter)
   [er2] = r0,r0 = 0
   qr0 = hex 10 00, adr(p3counterI), hex 00 00, hex 01 00
   [er2] = r0,r0 = 0

lbl p3for
   call 08B13
   eval(adr(ac) + 0x18)
   eval(adr(ac) + 0x18)
   call 10740

lbl p4
   qr0 = hex 0c f0, hex 02 00, eval(adr(p4base) + dist.main), hex 00 e4
   r0 = [er0]
   call 1D806           # r0 &= 0xf
   call 14F02
   r0 = [er0]
   call 24A20
   er0 *= r2,er2 = er0,er0 += er4,rt
   er8 = er0
   sp = [er8],pop er8

lbl p4write
   er0 = hex 0c f0
   r0 = [er0]
   call 0d88a
   er0 += 1,rt
   er2 = er0,er0 += er4,rt
   call 0E296
   eval(adr(p3for) + 0x4)
   hex 00 00
   sp = [er8],pop er8

lbl update
   hex fc ff
   hex 04 05 06 07 08 09 0a 0b 0c 0d 0e 0f
   hex 04 00
   hex 08 09 0a 0b 04 05 06 07 00 01 02 03
   hex 01 00
   hex 02 06 0a 0e 01 05 09 0d 00 04 08 0c
   hex ff ff
   hex 01 05 09 0d 02 06 0a 0e 03 07 0b 0f

lbl p1table
   hex 40 02
   hex 50 02
   hex 60 02
   hex 70 02
   hex 40 12
   hex 50 12
   hex 60 12
   hex 70 12
   hex 40 22
   hex 50 22
   hex 60 22
   hex 70 22
   hex 40 32
   hex 50 32
   hex 60 32
   hex 70 32

lbl p2table
   hex 80 04
   adr(update)
   eval(adr(p2main) - 0x2)
   hex 40 08
   eval(adr(update) + 0xe)
   eval(adr(p2main) - 0x2)
   hex 80 08
   eval(adr(update) + 0x1c)
   eval(adr(p2main) - 0x2)
   hex 40 04
   eval(adr(update) + 0x2a)
   eval(adr(p2main) - 0x2)
   hex 04 10
   hex 00 00
   adr(ac)
   eval(adr(ac) + 0x1c)

@section.launcher at 0xd180
hex fd 24 cc ea 34 2d 31