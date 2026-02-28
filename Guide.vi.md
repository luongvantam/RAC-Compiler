# RAC Compiler — Hướng dẫn sử dụng

---

## 1. Ghi chú (Comment)

Sử dụng ghi chú để giải thích mã nguồn. RAC hỗ trợ cả ghi chú 1 dòng và nhiều dòng.

```rsc
# Đây là ghi chú 1 dòng
/*
   Đây là ghi chú nhiều dòng
   có thể xuống dòng
*/
```

---

## 2. Chỉ thị (Directive)

### org

Đặt địa chỉ gốc cho mã máy.

```rsc
org 0xe9e0
```

---

## 3. Nhãn (Label)

Định nghĩa nhãn để nhảy hoặc tham chiếu.

```rsc
lbl start
  call 0x1234
  goto end
lbl end
```

---

## 4. Thêm dữ liệu (Data)

Thêm dữ liệu hex thô hoặc hex đảo byte.

```rsc
0x1234ABCD
hex CD AB 34 12
```

---

## 5. Gọi & Nhảy (Call & Jump)

Gọi địa chỉ, hàm tích hợp hoặc nhảy tới nhãn.

```rsc
call 0x5678
call print
goto start
```

---

## 6. Lấy địa chỉ (Address Of)

Lấy địa chỉ của nhãn (có thể cộng offset).

```rsc
adr(main)
eval(adr(loop) + 0x4)
```

---

## 7. Độ dài chương trình

Ghi độ dài chương trình tại vị trí này.

```rsc
pr_length
```

---

## 8. Chuỗi ký tự

Thêm chuỗi, hỗ trợ chèn biến bằng `{}`.

```rsc
var ten = "World"
"Xin~chào,~{ten}!"
```

**Lưu ý:** hãy sử dụng `~` để thay thế cho ` ` trong string.

---

## 9. Hàm (Function)

Định nghĩa khối mã tái sử dụng và gọi với tham số.

```rsc
func greet(person) {
  "Hello,~{person}!"
}

greet("Nam")
greet("Linh")
```

---

## 10. Eval (Tính toán biểu thức)

Tính toán biểu thức số học hoặc địa chỉ tại thời điểm biên dịch.

```rsc
eval(0x1 + 0x2 * 0x3)
eval(adr(label1) - adr(label2))
# ta có thể dùng calc() thay thế eval() vì chức năng như nhau
```

---

## 11. Biến & Thanh ghi

Định nghĩa biến (số, hex, chuỗi) và gán giá trị cho thanh ghi.

```rsc
var count = 10
var hexval = 0x1A2B
var message = "Test"
reg r1 = 0x5
r2 = 0xFF
```

Cách gọi biến sẽ là `varname` và áp dụng tương tự cho string.

---

## 12. Lệnh ghép (Compound Statement)

Ghép nhiều lệnh trên 1 dòng bằng `;`.

```rsc
call 0x1234 ; goto end
```

---

## 13. Key Mapping

Sử dụng hằng phím cho fx580vnx (xem key_map.txt để tra cứu).

```rsc
KEY_SHIFT
KEY_1
KEY_ADD
```

---

## 14. Functions Python

Định nghĩa một hàm Python, sau đó gọi và sử dụng hàm đó.

```rsc
org 0xe9e0

def check_even_odd(n) {
  if n%2==0{
    return 0x1      # Even
  } else {
    return 0x0      # Odd
  }
}

py.check_even_odd(0x2)
py.check_even_odd(0x3)
```

---

## 15. Vòng lặp

Lặp lại một tập hợp nào đó một số lần cố định trong quá trình biên dịch.

```rsc
loop 4 {
  0x67
}
hex 00 00
```

---

## 16. Find_gadgets

Tìm kiếm gadgets phù hợp

```rsc
find_gadgets {
  mov er{a[1]}, er{b[1]}
  pop pc
}
```
Dùng {var} để nêu ra 1 biến giả định có giá trị từ 0 đến 15, {var[1]} để nêu ra 1 biến giả định từ 0 đến 9.

---

## 17. Section

Section cho phép chia một file thành nhiều vùng độc lập.

```rsc
@set.main
org 0xe9e0
hex 30 30 30 30

@set.launcher
org 0xd180
xr0 = hex 30 30 30 30
```

---

## 18. Hệ thống mở rộng (Extension)

Bạn có thể định nghĩa cú pháp mới, macro qua `extensions.txt`.

**Ví dụ extension:**

```txt
---syntax---
print {msg}
---logic---
print(msg)
---output---
call print
```

---

## 19. Ví dụ hoàn chỉnh

```rsc
org 0xe9e0
var name = "Nguyen~Van~A"
lbl main
  "Hello,~{name}!"
  call print
```

---

Tác giả: luongvantam
