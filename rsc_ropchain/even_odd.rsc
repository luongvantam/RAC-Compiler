# AI Content

@section.main at 0xd730 backup 0xe9e0

# ==========================================================
# RAC Program: Even/Odd Checker
#
# Input: Biến A (var_a) — người dùng nhập trước bằng mode Calculate
# Output: In "EVEN" nếu A chẵn, "ODD" nếu A lẻ
#
# Thuật toán:
#   B = A - 2*Int(A/2)     (Lấy phần dư khi chia cho 2)
#   Nếu B == 0 → Chẵn (EVEN)
#   Nếu B == 1 → Lẻ (ODD)
# ==========================================================

lbl start
    setlr_pc
    setsfr

    # 1. Tính B = A - 2*Int(A÷2) bằng calc_func
    xr0 = adr(addr_calc), var_b
    calc_func

    # 2. Đọc byte đầu tiên của var_b (giá trị mantissa)
    #    Nếu B=0 thì byte 0 = 0x00, nếu B=1 thì byte 0 = 0x01
    er0 = var_b
    r0 = [er0]
    r1 = 0, rt

    # 3. So sánh er0 với 0 (nếu B == 0 thì EVEN)
    er2 = 0x0000
    er0 - er2_eq,r0 = 1|r0 = 0,rt

    # 4. Tra bảng load_table (r0=0 → lẻ, r0=1 → chẵn)
    er2 = adr(table_branch)
    load_table
    er14 = er0, pop xr0
    hex 00 00 00 00
    sp = er14, pop er14

lbl print_even
    xr0 = hex 01 01, adr(text_even)
    line_print
    render.ddd4
    brk

lbl print_odd
    xr0 = hex 01 01, adr(text_odd)
    line_print
    render.ddd4
    brk

lbl addr_calc
    adr(formula)

lbl formula
    'A-2Int(A÷2)'
    hex 00

lbl text_even
    "EVEN"
    hex 00 00

lbl text_odd
    "ODD"
    hex 00

lbl table_branch
    eval(adr(print_odd) - 0x2)      # r0 = 0: B != 0 → Lẻ
    eval(adr(print_even) - 0x2)     # r0 = 1: B == 0 → Chẵn

lbl end
    hex 00 00 00 00


@section.launcher at 0xd180

hex fd 24 30 30
setlr
setsfr
xr0 = 0xd730, 0xe9e0
call 09451
hex fe 01
er14 = 0xd72e
sp = er14, pop er14
