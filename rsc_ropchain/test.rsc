@section.main
org 0xd730
backup 0xe9e0

dist.main
lbl main
eval(adr(main) + dist.main)


def hello: 12345

hello

func main(h) {
    return eval(adr(h) - 0x2)
}

er0 = main(main)

sizeof(main)