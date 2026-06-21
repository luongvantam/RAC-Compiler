@section.main at 0xd730 backup 0xe9e0 as main_sec

# 1. Test gadget definitions
def {builtin} my_func_gadget : 0x13344

# 2. Test aliases
my_func_gadget as my_target

# 3. Test dynamic macros
def load_and_call(<reg>, <val>) => {
    <reg> = <val>
    call my_target
}

# 4. Test multi-line parentheses
def sum_hex(<a1>, <a2>) => eval(
    <a1> + <a2>
)

# 5. Test variable definitions
var initial_val = 0x0001
step_val = 0x0002

# 6. Test function definition with return
func get_next_addr(h) {
    return eval(adr(h) - 0x02)
}

# 7. Test regular function (void body)
func print_two_status(msg1, msg2) {
    call my_target
}

# 8. Test macro register assignments
def clear_regs(<r1>, <r2>) => {
    <r1> = 0x0000
    <r2> = 0x0000
}

lbl start
    # Test compound statement and backslash continuation
    er0 = sum_hex(initial_val, step_val); hex 00 \
    00

    # Test dynamic macro usage
    load_and_call(er2, 0xd73c)

    # Test function with return assigned to register
    er4 = get_next_addr(start)

    # Test void function usage
    print_two_status(initial_val, step_val)

    # Test macro register assignment
    clear_regs(er6, er8)

    # Test list command and evaluation
    [
        0x90
        0xfc
    ]

    # Test string command and templates
    var score_val = 0x0003
    lbl info_text
        "Score: {score_val}"
        hex 00

    # Test loops and repeat blocks
    loop 2 {
        hex aa
    }

    # Test sizeof, dist, and pr_length calculations
    er10 = sizeof(main_sec)
    er12 = dist.main_sec
    er14 = eval(pr_length)

    # Test goto jumps
    goto end_label

lbl end_label
    hex ff ff