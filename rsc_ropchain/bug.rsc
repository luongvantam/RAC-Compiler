@section.main at 0xd730 backup 0xe9e0

lbl main
    hex 00 00
lbl main2
    hex 00 00
    hex ff ff
adr_arith main2 + adr_arith main

pr_org()
pr_backup()