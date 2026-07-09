@section.main at 0xd730 backup 0xe9e0
/*
bool is_prime(n) {
    if (n < 2) return false;
    for (i = 2; i <= n / i; i++) {
        if (n - (n / i) * i == 0) return false;
    }
    return true;
}
*/

# var_a = input
# var_x = loop_i

lbl start
    setlr_pc
    setsfr
    clear()

lbl main
    
    
lbl adr_check
    adr(check)

lbl check
    'A - ( A / x ) * x _'