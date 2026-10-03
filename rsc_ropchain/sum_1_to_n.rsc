# AI Content

@section.main at 0xd730 backup 0xe9e0

# ==========================================================
# RAC Program: Sum 1 to n (where n is stored at 0xd400)
# Correct Gadget Math: S = n * (n + 1) / 2
# - er0 = n + 1
# - er2 = n (so r2 = n)
# - er4 = 0
# - Gadget 14bd4 (er0 *= r2, er2 = er0, er0 += er4, rt):
#     er0 = (n + 1) * n + 0 = n * (n + 1)
# - Gadget 28c54 (er0 /= r2, rt) with er2 = 2:
#     er0 = n * (n + 1) / 2
# Result is stored at 0xd402 and rendered on screen
# ==========================================================

lbl start
    setlr_pc
    setsfr

lbl read_n
    # 1. Đọc giá trị n (16-bit) từ địa chỉ chẵn 0xd400 vào er0
    er2 = 0xd400
    er0 = [er2],r2 = 9,rt

lbl compute_sum
    # 2. er2 = n (lưu n vào er2 để lấy r2 làm số nhân)
    er2 = 0x0000
    er2=er0,er0=er2,pop er8,rt
    hex 00 00                   # Dummy cho pop er8 (er8 = 0)
    
    # 3. er0 = n + 1
    er0++,rt
    
    # 4. er4 = 0 (phần bù cộng thêm = 0)
    er4 = 0x0000
    
    # 5. Nhân: er0 = (n + 1) * r2 + er4 = (n + 1) * n + 0
    # Gadget 14bd4: er0 *= r2,er2 = er0,er0 += er4,rt
    er0*=r2,er2=er0,er0+=er4,rt
    
    # 6. Chia 2: er0 = er0 / 2 (S = n * (n + 1) / 2)
    # Gadget 28c54: er0/=r2,rt
    er2 = 0x0002
    er0/=r2,rt

lbl store_result
    # 7. Ghi kết quả er0 vào địa chỉ chẵn 0xd402
    er2 = 0xd402
    er4 = 0x0000
    [er2]=er0,r2=0,pop er4,rt
    hex 00 00                   # Dummy cho pop er4

lbl display
    # 8. Hiển thị thông báo lên màn hình LCD
    # line_print: xr0 = (x, y, text_addr)
    # y = 1 (dòng 1), x = 1 (cột 1)
    xr0 = hex 01 01, adr(msg)
    line_print
    render.ddd4
    brk

lbl msg
    "Tổng 1..n đã tính!"
    hex 00 00

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
