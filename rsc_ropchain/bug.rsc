org 0xd730
backup 0xe9e0

lbl test
    er0 = adr(test, 0, 0xe9e0)
    brk

@section.launcher at 0xd180
str "nothing"