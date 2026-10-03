# AI Content

@section.main at 0xd730 backup 0xe9e0

# ==========================================================
# RAC Program: Key Switch-Case (Press 1 -> A, 2 -> B, 3 -> C)
#
# Key Insights & Optimizations:
# 1. Sử dụng trực tiếp `ea = adr(table)` thay vì gọi `xr12 + call 17CA6`
#    -> Tiết kiệm 10 bytes header `hex 00 00 00 00 00 00 00 00 00 00` trong bảng!
# 2. `getscancode` là hàm ROM phá hỏng bộ nhớ ngăn xếp (stack payload)
#    -> Cần có nhãn `restore` sao chép lại payload từ `0xe9e0` về `0xd730`
#       trước khi pivot SP quay lại vòng lặp đọc phím!
# ==========================================================

lbl start
    setlr_pc
    setsfr

lbl read_input
    # 1. Đọc phím vào ô nhớ `key`
    er0 = adr(key)
    getscancode
    setlr_pc                     # Khôi phục LR sau khi getscancode chạy
    
    # 2. Gán trực tiếp ea = adr(table) (gọn gàng, không cần header 10 byte)
    ea = adr(table)
    pop er0
    lbl key
        hex 00 00
    call 09C20
    call 1C64A                   # ea_switchcase lookup
    sp = er6, pop er8            # Nhảy tới handler tương ứng

lbl handle_key_1
    # Nhấn 1 -> In "A"
    xr0 = hex 01 01, adr(text_a)
    line_print
    render.ddd4
    er14 = eval(adr(restore) - 0x2)
    sp = er14, pop er14

lbl handle_key_2
    # Nhấn 2 -> In "B"
    xr0 = hex 01 01, adr(text_b)
    line_print
    render.ddd4
    er14 = eval(adr(restore) - 0x2)
    sp = er14, pop er14

lbl handle_key_3
    # Nhấn 3 -> In "C"
    xr0 = hex 01 01, adr(text_c)
    line_print
    render.ddd4
    er14 = eval(adr(restore) - 0x2)
    sp = er14, pop er14

lbl handle_exit
    # Nhấn AC -> Dừng
    brk

lbl restore
    # Khôi phục toàn bộ payload sạch từ backup 0xe9e0 về 0xd730
    di, rt
    xr0 = 0xd730, 0xe9e0
    call 09451                   # memcpy gadget
    hex fe 01
    er14 = 0xd72e                # adr(read_input) - 2
    sp = er14, pop er14          # Pivot SP vào payload sạch!

lbl text_a
    "A"
    hex 00

lbl text_b
    "B"
    hex 00

lbl text_c
    "C"
    hex 00

lbl table
    # Bảng switch-case trực tiếp từ [ea] (Không cần header 10 bytes!)
    key_1
    eval(adr(handle_key_1) - 0x2)
    
    key_2
    eval(adr(handle_key_2) - 0x2)
    
    key_3
    eval(adr(handle_key_3) - 0x2)
    
    key_ac
    eval(adr(handle_exit) - 0x2)
    
    # Default (Else): Khôi phục và đọc tiếp
    hex 00 00
    eval(adr(restore) - 0x2)

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
