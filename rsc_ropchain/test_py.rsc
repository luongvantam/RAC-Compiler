org 0xe9e0

def logic_delay_py(value) {
    val_str = str(value).strip()
    if val_str.lower().startswith("0x") {
        val_int = int(val_str, 16)
    } else {
        val_int = int(val_str, 10)
    }
    return f"0x{val_int:04x}"
}

func delay_from_rsc(value) {
    pop er0
    py.logic_delay_py(value)
    delay
}

delay_from_rsc(0x111)