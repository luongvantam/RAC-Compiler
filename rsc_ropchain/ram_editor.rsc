@set.main
org 0xe3b6 #e3d4
#inject c580, override
#backup 0xe9e0
#3 comment là là của auto hc-inj

dista=eval(0xe63e-0xe3d4)

lbl backup  #backup 
  
  0x0386
  0xe9fe
  0xe63e
  eval(adr(loop)-2+dista)
  call 18932
  0x3030
  xr0=0xd111, 0x0202
  [er0]=r2
  sp=er6,pop er8
  
lbl home  #e3d4
  setlr_pc
  buffer_clear
  setsfr
  r0=8
  call 208a0
lbl autopage
  er4=0xc030
  er2=eval(adr(addr)+dista)
  er0=[er2],r2=9,rt
lbl param2
  and r0, r5,pop r4,rt
  0x3030
  er2=er0,er0+=er4,rt
  er0=eval(adr(print)+4+dista)
  [er0]=er2,rt
  er0=eval(adr(print)+4)
  [er0]=er2,rt
lbl print #💀💀
  er0=0xd000
lbl offset_adr
  er8=0x0000
  ea=eval(adr(stradr)+dista)
  er0+=er8,rt
  er8=er0
  r0=r1,rt
  hex_byte
  [ea+]=er0
  er0=er8
  er2=eval(adr(print_byte)+4)
  [er2]=er0,r2 = 0,pop er4,rt
  0x3030
  hex_byte
  [ea+]=er0
lbl y_adr
  xr0=0x0100, eval(adr(stradr)+dista)
  BL line_print
  setlr_pc
lbl print_byte
  er0=0x3030
lbl offset_byte
  er8=0x0000
  er0+=er8,rt
  er8=er0
  er2=eval(adr(addr)+dista)
  er0=[er2],r2=9,rt
  er2=er0,er0+=er4,rt
  er0=er8
  call 9b76
  r1=0,rt
  er2=0x3004
  er0*=r2,er2 = er0,er0+=er4,rt
  er0=0xd138
  [er0]=r2
  er0=er8
  r0=[er0]
  hex_byte
  er2=er0,er0+=er4,rt
  er0=eval(adr(strbyte)+dista)
  [er0]=er2,rt
  
lbl x_byte
  xr0=0x0120, eval(adr(strbyte)+dista)
  bL line_print
  er14=eval(adr(next)-2)
  call 981a
lbl next
  eval(adr(smallloop)-2+dista)
  er0=adr(wth)
lbl test
  #getkey
  nop
  setlr_pc
  pop xr0
lbl wth
  0x3030
  0x3030
  call 9b76
  r1=0,rt
  er2=eval(adr(loopgetkey)+dista)
  er0+=er0,er2+=er0,er0=[er2]
  er2=er0,er0+=er4,rt
  er0=adr(shh)
  [er0]=er2,rt
  xr0=adr(getkey), hex 84 ac
lbl shh
  pop qr8
  setlr_pc
  er4=adr(counter_print_byte)
  [er4]+=1,rt
  er4=eval(adr(offset_byte)+4+dista)
  [er4]+=1,rt
  er8=eval(adr(x_byte)+4+dista)
  er2=0x0012
  [er8]+=er2,pop xr8
  eval(adr(x_byte)+4+dista)
  0x3030
  di,rt
lbl counter_print_byte
  call 1073a
  eval(adr(bigloop)-2+dista)
  er2=0x3020
  er0=er8
  [er0]=r2
  xr0=eval(adr(offset_byte)+4+dista), 0x3000
  [er0]=r2
  
  er4=adr(counter_print_adr)
  [er4]+=1,rt
  er8 = eval(adr(y_adr)+4+dista)
  er2=0x0800
  [er8]+=er2,pop xr8
  eval(adr(x_byte)+4+dista)
  0x3030
  er2=0x0800
  [er8]+=er2,pop xr8
  eval(adr(offset_adr)+4+dista)
  0x3030
  er2=0x0008
  [er8]+=er2,pop xr8
  0x30303030
lbl counter_print_adr
  call 1073a
  0x3030
  xr0=eval(adr(x_byte)+4+dista), 0x0120
  [er0]=er2,rt
  xr0=eval(adr(offset_adr)+4+dista), 0x0000
  [er0]=er2,rt
  xr0=eval(adr(y_adr)+4+dista), 0x0100
  [er0]=er2,rt
  render.ddd4
lbl getkey
  nop  # hex ac 84
  getkeycode
  sp+=20
  pop xr0
lbl key
  0x3030
  0x83da
  cvt_key
  er2=er0,er0+=er4,rt
  nop
  setlr_pc
  er0=0xd10e
  [er0]=er2,rt
  call 1d94a
  ea=eval(adr(taebl)+dista)
  cmp_ea
  er6=[ea+]
  er0=er8
  sp = er6,pop er8
lbl packinit
  er2=0xd10e
  er0=[er2],r2=9,rt
  er2=eval(adr(pack)+dista)
  [er2]=r0,r2=0
  getkeycode
  er14=eval(adr(space)-2+dista)
  sp=er14,pop er14
lbl space
  setlr_pc
  er0=0xd10e
  [er0]=er2,rt
  er0=eval(adr(pack)+1+dista)
  [er0]=r2
  call 1d94a
  ea=eval(adr(table2)+dista)
  cmp_ea
  er6=[ea+]
  er0=er8
  sp = er6,pop er8
lbl initpack2
  pop xr0
lbl pack
  0x0000
  eval(adr(val)+dista)
  call 20840
  r0=r1,rt
  [er2]=r0,r2=0
  pop xr0
lbl addr
  0xd552
lbl val
  0x0000
  [er0]=r2
  er0=0x0001
  sp+=30,pop er14
lbl key_check
  er2=0xd10e
  er0=[er2],r2=9,rt
  ea=eval(adr(key_table)+dista)
  cmp_ea
  er6=[ea+]
  er0=er8
  sp=er6,pop er8
lbl add
  er8=eval(adr(addr)+dista)
  er2=er0,er0+=er4,rt
  [er8]+=er2,pop xr8
lbl loopgetkey
  hex d8 39
  hex 32 36
lbl loop
  pop xr4, pop xr12
  adr(home)
  0x0268
  0xe63e
  eval(adr(home)-12)
  memcpy_auto_jmp
lbl bigloop
  pop xr4, pop xr12
  adr(print)
  0x0186
  # 0x0140
  eval(adr(print)+dista)
  eval(adr(print)-12)
  memcpy_auto_jmp
lbl smallloop
  pop xr4, pop xr12
  adr(offset_byte)
  0x00e0
  # 0x009e
  eval(adr(offset_byte)+dista)
  eval(adr(print_byte)-12)
  memcpy_auto_jmp
lbl byebye
  ea=eval(adr(addr)+dista)
  er6=[ea+]
  sp=er6,pop er8
lbl key_table
  0xfc1c
  eval(adr(add)-2+dista)
  0xfff8
  0xfc1d
  eval(adr(add)-2+dista)
  0x0008
  0xfc1e
  eval(adr(add)-2+dista)
  0x0001
  0xfc1f
  eval(adr(add)-2+dista)
  0xffff
  0x00a6
  eval(adr(add)-2+dista)
  0x0040
  0x00a7
  eval(adr(add)-2+dista)
  0xffc0
  0x00a8
  eval(adr(add)-2+dista)
  0x0100
  0x00a9
  eval(adr(add)-2+dista)
  0xff00
  0xfc26
  eval(adr(byebye)-2+dista)
  0x0000
  eval(adr(loop)-2+dista)
lbl taebl
  0xd130
  eval(adr(packinit)-2)
  0x0000
  eval(adr(key_check)-2+dista)
lbl table2
  0xe830
  eval(adr(initpack2)-2+dista)
  0x0000
  eval(adr(key_check)-2+dista)
lbl stradr
  hex 3030 3030 3A00
lbl strbyte
  hex 30 30 00
lbl thamchieu
  
@set.launcher1
org 0xd180
  hex fd 24
  0xe9d8
  sp=er14,pop qr8,pop qr0
  hex 23

@set.launcher2
org 0xd180
dista=eval(0xe63e-0xe3d4)

hex fd24
0xe9ec
pop qr0
0x0386
0xe9fe
0xe63e
eval(0xe6b2-2+dista)
call 18932
0x3030
sp=er14,pop er14
hex 23