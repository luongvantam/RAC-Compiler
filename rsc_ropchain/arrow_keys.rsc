# AI Content

@section.main at 0xd730 backup 0xe9e0

# ==========================================================
# RAC Program: Arrow Key Direction Detector
#
# Nhấn phím mũi tên trên máy tính Casio fx-580VN X:
#   ↑ (Up)    -> In "UP"
#   ↓ (Down)  -> In "DOWN"
#   ← (Left)  -> In "LEFT"
#   → (Right) -> In "RIGHT"
#   AC        -> Thoát chương trình
#
# Kỹ thuật sử dụng:
# - getscancode: Đọc phím có debounce (nhấn giữ chỉ nhận 1 lần)
# - ea = adr(table): Gán trực tiếp ea, bỏ 10-byte header
# - restore + memcpy: Khôi phục payload sau mỗi lần getscancode phá stack
# - setlr_pc sau getscancode: Khôi phục LR vì getscancode dùng BL nội bộ
# ==========================================================

lbl start
    setlr_pc
    setsfr

lbl read_input
    er0 = adr(key)
    getscancode
    setlr_pc

    ea = adr(table)
    pop er0
    lbl key
        hex 00 00
    call 09C20                   # cmp_ea: quét bảng tìm key
    call 1C64A                   # er6 = [ea+]: lấy địa chỉ handler
    sp = er6, pop er8            # nhảy tới handler

lbl handle_up
    xr0 = hex 01 01, adr(text_up)
    line_print
    render.ddd4
    er14 = eval(adr(restore) - 0x2)
    sp = er14, pop er14

lbl handle_down
    xr0 = hex 01 01, adr(text_down)
    line_print
    render.ddd4
    er14 = eval(adr(restore) - 0x2)
    sp = er14, pop er14

lbl handle_left
    xr0 = hex 01 01, adr(text_left)
    line_print
    render.ddd4
    er14 = eval(adr(restore) - 0x2)
    sp = er14, pop er14

lbl handle_right
    xr0 = hex 01 01, adr(text_right)
    line_print
    render.ddd4
    er14 = eval(adr(restore) - 0x2)
    sp = er14, pop er14

lbl handle_exit
    brk

lbl restore
    di, rt
    xr0 = 0xd730, 0xe9e0
    call 09451
    hex fe 01
    er14 = eval(adr(read_input) - 0x2)
    sp = er14, pop er14

lbl text_up
    "UP"
    hex 00 00

lbl text_down
    "DOWN"
    hex 00 00

lbl text_left
    "LEFT"
    hex 00 00

lbl text_right
    "RIGHT"
    hex 00

lbl table
    key_up
    eval(adr(handle_up) - 0x2)

    key_down
    eval(adr(handle_down) - 0x2)

    key_left
    eval(adr(handle_left) - 0x2)

    key_right
    eval(adr(handle_right) - 0x2)

    key_ac
    eval(adr(handle_exit) - 0x2)

    # Default: khôi phục và đọc tiếp
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
