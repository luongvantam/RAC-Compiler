@set.main
org 0xe9e0

find_gadgets {
    mov er{a[1]}, er{b[1]}
    pop pc
}

@set.launcher
org 0xd180

xr0 = hex 30 30 30 30