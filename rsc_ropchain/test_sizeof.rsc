@section.main
org 0xd730
hex 01020304
pr_length
sizeof()
sizeof(main)
sizeof(other)

@section.other
org 0xd750
hex 050607
sizeof(main)
sizeof()
eval(0x10 + sizeof(main))
eval(0x10 + sizeof())