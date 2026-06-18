@section.main
org 0xd730
pr_length
sizeof()
sizeof(main)
sizeof(other)

@section.other
org 0xd750
sizeof(main)
sizeof()
pr_length
eval(sizeof(main) + 0x4)
eval(pr_length + 0x2)