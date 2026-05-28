@section.main
org 0xe9e0

var dista = 0x100
var text = "world"

func main(a) {
    a
}

lbl main
    er0 = hex 30 30
    er2 = adr_of text
    er4 = eval(adr(text) + dista)
    call line_print
    main(0x02)
    loop 4 {
        hex 30
    }

    KEY_0
    KEY_1
    KEY_2

text:
    "hello, {text}"

'sin( 9 0 )'