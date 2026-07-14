# hello hello
/*
hello
*/

@section.main at 0xd730 backup 0xe9e0

func main2(a, b=0x02, c=0x03) {
    a; b; c
}

main2(0x01)

func main(a, b=0x02) {
    return eval(a+b)
}

main(0x01)

repeat 4 { hex 30 30 }
loop 4 {
    hex 00
}

adr($)

@set.test at 0xd180