@set.test at 0x1000

lbl main_label
func abc() {
    return 1
}

repeat 5 {
    str "hello"
}

goto main_label
def main_gadget: 0x1000
adr(main_label)
str "hello"
