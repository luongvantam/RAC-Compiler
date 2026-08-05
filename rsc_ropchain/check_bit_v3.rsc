lbl main
  er2 = adr(funcpos)
  call 087bc
  er2 = adr(funcbit)
  [er2] = r0

  pop er0, pop er4
  lbl funcpos
    hex 00 00
  lbl funcbit
    hex 44 01
  
  call 14BD6            # er2 = er0, er0 += er4, rt
  r5 >> r4, r0 |= r5, pop r4, rt
  hex 00 00
  
  er0 = [er2], r2 = 9, rt
  r0 &= r5, pop r4, rt
  hex 00 00