# AI Content

@section.main at 0xd730 backup 0xe9e0

# ==========================================================
# RAC Program: Sum 1 to n (Compact ROP Loop via qr0/xr0)
#
# Optimization:
# - Use `qr0 = er0, er2, er4, er6` (12 bytes vs 24 bytes)
# - Use `xr0 = er0, er2` (8 bytes vs 12 bytes)
# - Trade execution time for absolute minimal bytecode size
# ==========================================================

lbl start
    setlr_pc
    setsfr

lbl init
    # Khởi tạo: er0 = 0 (giá trị sum ban đầu), er2 = 0xd402, er4 = 0, er6 = 0
    # Gói gọn 4 thanh ghi vào 1 gadget pop qr0 duy nhất (tiết kiệm 12 byte!)
    qr0 = 0x0000, 0xd402, 0x0000, 0x0000
    [er2]=er0,r2=0,pop er4,rt
    hex 00 00

lbl loop_start
    # 1. Đọc sum từ 0xd402 vào er0, lưu vào er4
    er2 = 0xd402
    er0 = [er2],r2 = 9,rt
    er4 = 0x0000
    er4+=er0,r8=r8,rt           # er4 = sum
    
    # 2. Đọc counter từ 0xd400 vào er0 và cộng vào sum
    er2 = 0xd400
    er0 = [er2],r2 = 9,rt       # er0 = counter
    er0+=er4,rt                 # er0 = sum + counter
    
    # 3. Ghi sum_new vào 0xd402
    er2 = 0xd402
    er4 = 0x0000
    [er2]=er0,r2=0,pop er4,rt
    hex 00 00
    
    # 4. Đọc counter từ 0xd400, giảm 1
    er2 = 0xd400
    er0 = [er2],r2 = 9,rt
    er2 = 0x0001
    er0 -= er2,rt               # er0 = counter - 1
    
    # 5. Ghi counter mới vào 0xd400
    er2 = 0xd400
    er4 = 0x0000
    [er2]=er0,r2=0,pop er4,rt
    hex 00 00
    
    # 6. So sánh counter với 0:
    er2 = 0x0000
    er0 - er2_eq,r0 = 1|r0 = 0,rt
    
    # 7. Nhảy JumpSP qua load_table:
    er2 = adr(table_loop)
    load_table
    er14 = er0, pop xr0
    hex 00 00 00 00
    sp = er14, pop er14

lbl table_loop
    eval(adr(loop_start) - 0x2) # Index 0 (r0 = 0: tiếp tục lặp)
    eval(adr(loop_done) - 0x2)  # Index 1 (r0 = 1: thoát lặp)

lbl loop_done
    # Hiển thị thông báo hoàn thành
    xr0 = hex 01 01, adr(msg)
    line_print
    render.ddd4
    brk

lbl msg
    "Loop sum xong!"
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
