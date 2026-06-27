@section.main
org 0xd730
backup 0xe9e0
dist.main
lbl main
eval(adr(main) + dist.main)
func main(h) {
    return eval(adr(h) - 0x2)
}
er0 = main(main)
sizeof(main)
lbl text = "text"

@section.main2
org 0xd750
backup 0xea00
lbl start
adr(start,dist.main2, 0xe9e0)




