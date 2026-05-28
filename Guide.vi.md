# TÀI LIỆU HƯỚNG DẪN SỬ DỤNG RAC COMPILER

---

## GIỚI THIỆU CHUNG
**RAC Compiler** là một bộ biên dịch mã nguồn (compiler) và hợp dịch (assembler) chuyên dụng, được thiết kế để phát triển, tối ưu hóa và đóng gói mã máy cho các hệ thống nhúng, đặc biệt là môi trường giả lập hoặc các dòng máy tính bỏ túi (như fx-580VN X). Tài liệu này cung cấp hướng dẫn chi tiết về cú pháp, chỉ thị biên dịch, cấu trúc điều khiển và các tính năng mở rộng của ngôn ngữ RSC.

---

## PHẦN I: CÚ PHÁP VÀ CẤU TRÚC DỮ LIỆU CƠ BẢN

### 1. Ghi chú (Comments)
Hệ thống ghi chú giúp nhà phát triển giải thích thuật toán, cấu trúc mã hoặc vô hiệu hóa các đoạn mã trong quá trình gỡ lỗi (debug). RAC hỗ trợ hai loại ghi chú tiêu chuẩn:

* **Ghi chú một dòng (Single-line Comment):** Bắt đầu bằng ký tự `#`. Toàn bộ nội dung phía sau ký tự này trên cùng một dòng sẽ bị trình biên dịch bỏ qua.
* **Ghi chú nhiều dòng (Multi-line Comment):** Bắt đầu bằng `/*` và kết thúc bằng `*/`. Thích hợp cho việc giải thích các khối mã logic phức tạp hoặc viết tài liệu tích hợp.

```assembly
# Đây là ghi chú một dòng dùng để giải thích nhanh
/*
   Đây là ghi chú nhiều dòng.
   Trình biên dịch RAC sẽ bỏ qua toàn bộ khối này
   cho đến khi gặp ký tự đóng.
*/

```

### 2. Biến số và Quản lý thanh ghi (Variables & Registers)

RAC phân biệt rõ ràng giữa biến số (lưu trữ giá trị biên dịch) và thanh ghi (đại diện cho các ô nhớ vật lý/giả lập của kiến trúc đích).

* **`var`:** Định nghĩa biến, hỗ trợ các kiểu dữ liệu: Số nguyên, Số Hex, Chuỗi ký tự. Gọi biến bằng cách nhập trực tiếp tên biến.
* **`reg`:** Khởi tạo hoặc gán giá trị trực tiếp cho một thanh ghi phần cứng chương trình.

```assembly
var count = 10          # Biến số nguyên thập phân
var hexval = 0x1A2B     # Biến số hệ thập lục phân (Hex)
var message = "Test"    # Biến chuỗi

reg r1 = 0x5            # Khởi tạo thanh ghi r1 với giá trị ban đầu là 0x5
r2 = 0xFF               # Gán trực tiếp giá trị 0xFF cho thanh ghi r2

```

### 3. Xử lý chuỗi ký tự (String Literals)

RAC hỗ trợ định nghĩa chuỗi ký tự và tính năng **String Interpolation** (chèn giá trị của biến vào chuỗi) thông qua cú pháp `{ten_bien}`.

* **Quy tắc đặc biệt:** Do cơ chế phân tách cú pháp của RAC, khoảng trắng (` `) trong chuỗi bắt buộc phải được thay thế bằng ký tự ngã (`~`). Khi biên dịch, ký tự `~` sẽ được chuyển đổi ngược lại thành ký tự khoảng trắng tiêu chuẩn (`0x20`).

```assembly
var ten = "World"
"Xin~chào,~{ten}!"  # Chuỗi kết quả sau biên dịch: "Xin chào, World!"

```

### 4. Cấu trúc Mảng / Danh sách (Arrays)

RAC hỗ trợ định nghĩa danh sách phần tử (Mảng dữ liệu) dưới hai kiểu định dạng: viết tường minh theo khối dòng hoặc viết ngắn gọn trên một dòng đơn.

```assembly
# Kiểu 1: Khai báo mảng nhiều dòng (Khối)
[
  0x1
  0x2
]

# Kiểu 2: Khai báo mảng một dòng (Inline), phân tách bằng dấu chấm phẩy `;`
[0x1; 0x2]

```

### 5. Chuỗi Token (Token Strings)

Sử dụng dấu nháy đơn `'...'` để định nghĩa một chuỗi biểu thức dạng thẻ Token. Trình phân tích cú pháp (Parser) của RAC sẽ giữ nguyên định dạng cấu trúc này để phục vụ xử lý riêng biệt trong các hàm macro hoặc toán tử phân tích chuỗi toán học.

```assembly
'sin( 90 )' # Chuỗi token phục vụ phân tích cú pháp biểu thức

```

---

## PHẦN II: LUỒNG ĐIỀU KHIỂN VÀ ĐỊNH NGHĨA HÀM

### 6. Nhãn định danh (Labels)

Nhãn (Label) được sử dụng để đánh dấu một vị trí cụ thể trong mã nguồn, tạo điều kiện cho các lệnh điều hướng như rẽ nhánh, nhảy hoặc gọi hàm tham chiếu tới mà không cần tính toán thủ công địa chỉ byte.

* **Cú pháp:** `lbl <tên_nhãn>`

```assembly
lbl start
  call 0x1234  # Gọi chương trình con tại địa chỉ 0x1234
  goto end     # Nhảy không điều kiện đến nhãn 'end'

lbl end        # Điểm đích của lệnh nhảy

```

### 7. Lệnh gọi và Nhảy (Call & Jump)

Đây là các lệnh điều khiển luồng thực thi cơ bản trong RAC, cho phép chuyển đổi ngữ cảnh chương trình tới một địa chỉ tuyệt đối, một hàm hệ thống hoặc một nhãn cục bộ.

* **`call <địa_chỉ / tên_hàm>`:** Gọi một chương trình con hoặc hàm tích hợp (built-in). Sau khi hàm thực thi xong, luồng chương trình quay trở lại lệnh kế tiếp.
* **`goto <tên_nhãn>`:** Nhảy không điều kiện tới nhãn được chỉ định trong phạm vi tệp.

```assembly
call 0x5678    # Gọi hàm tại địa chỉ tuyệt đối 0x5678
call print     # Gọi hàm hệ thống tích hợp sẵn có tên là 'print'
goto start     # Vòng lặp vô hạn, quay trở lại nhãn 'start'

```

### 8. Lệnh ghép trên một dòng (Compound Statements)

Để tối ưu hóa cấu trúc tệp mã nguồn mã nguồn ngắn gọn hơn, RAC cho phép viết nhiều câu lệnh trên cùng một dòng. Các câu lệnh này được phân tách với nhau bằng dấu chấm phẩy `;`.

```assembly
call 0x1234 ; goto end  # Thực thi lệnh call trước, sau đó lập tức thực hiện lệnh goto

```

### 9. Định nghĩa và Gọi hàm hệ thống (RAC Functions)

Hàm (Function) giúp module hóa mã nguồn, tăng khả năng tái sử dụng. Hàm trong RAC chấp nhận các tham số truyền vào và có thể xử lý các logic chuỗi hoặc mã máy bên trong dấu ngoặc nhọn `{}`.

```assembly
# Định nghĩa hàm 'greet' với một tham số 'person'
func greet(person) {
  "Hello,~{person}!"
}

# Lời gọi hàm với các đối số khác nhau
greet("Nam")
greet("Linh")

```

---

## PHẦN III: QUẢN LÝ BỘ NHỚ VÀ CHỈ THỊ BIÊN DỊCH

### 10. Chỉ thị vị trí gốc (Directive `org`)

Chỉ thị `org` (Origin) xác định địa chỉ vùng nhớ tuyệt đối nơi mã máy bắt đầu được nạp và thực thi. Đây là chỉ thị bắt buộc khi làm việc với các hệ thống có cấu trúc bộ nhớ cố định.

* **Cú pháp:** `org <Địa_chỉ_Hex>`
* **Ứng dụng:** Định vị chính xác entry-point cho firmware hoặc shellcode.

```assembly
org 0xe9e0  # Đặt địa chỉ gốc của chương trình tại vùng nhớ 0xE9E0

```

### 11. Chèn dữ liệu thô (Raw Data Insertion)

RAC cho phép lập trình viên nhúng trực tiếp dữ liệu nhị phân hoặc giá trị Hex vào tệp thực thi cuối cùng. Tính năng này hỗ trợ cả định dạng Big-Endian và Little-Endian (thông qua lệnh đảo byte).

* **Chèn Hex trực tiếp (Big-Endian):** Nhập trực tiếp giá trị định dạng `0x`.
* **Chèn Hex đảo byte (Little-Endian / Byte Stream):** Sử dụng từ khóa `hex` theo sau là các cặp byte phân tách bằng khoảng trắng.

```assembly
0x1234ABCD      # Chèn trực tiếp chuỗi 4 byte theo thứ tự xuất hiện
hex CD AB 34 12 # Chèn chuỗi byte dưới dạng mảng (thường dùng cho cấu trúc mã máy đảo byte)

```

### 12. Lấy địa chỉ và Tính toán Offset (Address Of & Evaluation)

Trong quá trình biên dịch, RAC hỗ trợ việc trích xuất địa chỉ bộ nhớ động của một nhãn thông qua hàm `adr()` và tính toán offset (khoảng cách dịch chuyển vùng nhớ) theo thời gian thực (compile-time) bằng từ khóa `eval()`.

* **`adr(label)`:** Trả về địa chỉ của `label`.
* **`eval(expression)`:** Tính toán giá trị của biểu thức toán học chứa địa chỉ nhãn trước khi xuất file nhị phân.

```assembly
adr(main)               # Lấy địa chỉ tĩnh của nhãn 'main'
eval(adr(loop) + 0x4)   # Lấy địa chỉ nhãn 'loop' và cộng thêm 4 byte offset

```

### 13. Phân vùng bộ nhớ (Sections)

Chỉ thị `@section` và `@set` cho phép người viết mã chia nhỏ chương trình thành các vùng độc lập, nạp vào các phân vùng bộ nhớ khác nhau trong cùng một lần biên dịch. Kỹ thuật này rất hữu ích khi xây dựng hệ thống có vùng khởi động (Launcher) và vùng thực thi chính (Main program) tách biệt.

```assembly
@set.main              # Kích hoạt ngữ cảnh phân vùng main
org 0xe9e0             # Cấu hình địa chỉ gốc của vùng main
hex 30 30 30 30

@section.launcher at 0xd180  # Định nghĩa phân vùng mới tên là 'launcher' tại địa chỉ tĩnh 0xD180
xr0 = hex 30 30 30 30        # Gán mảng byte cho thanh ghi xr0 thuộc vùng launcher

```

### 14. Ghi nhận độ dài chương trình (`pr_length`)

Từ khóa `pr_length` là một biến đặc biệt của trình biên dịch. Khi biên dịch, RAC sẽ tự động tính toán tổng dung lượng (tính bằng byte) của toàn bộ chương trình và ghi giá trị đó vào chính vị trí đặt từ khóa này.

```assembly
pr_length  # Trình biên dịch sẽ ghi đè kích thước file (ví dụ: 0x00A2) tại vị trí này

```

---

## PHẦN IV: TỐI ƯU HÓA VÀ HỆ THỐNG MỞ RỘNG

### 15. Tính toán biểu thức biên dịch (Compile-time Evaluation)

Từ khóa `eval()` hoặc `calc()` được sử dụng để thực hiện các phép toán số học, logic hoặc xử lý con trỏ địa chỉ ngay tại thời điểm biên dịch. Điều này giúp tối ưu hóa hiệu năng, giảm tải việc tính toán khi chương trình chạy (run-time).

> 💡 **Lưu ý:** `eval()` và `calc()` có chức năng hoàn toàn tương đương và có thể thay thế cho nhau tùy thuộc vào thói quen viết mã của bạn.

```assembly
eval(0x1 + 0x2 * 0x3)           # Trả về giá trị 0x7 (áp dụng đúng thứ tự toán tử)
calc(adr(label1) - adr(label2)) # Tính khoảng cách (kích thước) byte giữa hai nhãn

```

### 16. Vòng lặp biên dịch (Compile-time Loops)

Cú pháp `loop` cho phép nhân bản một khối mã hoặc lặp đi lặp lại một chuỗi byte dữ liệu theo số lần chỉ định sẵn trong quá trình build file, tránh việc phải copy-paste mã thủ công.

* **Cú pháp:** `loop <Số_lần> { <Khối_lệnh/Dữ_liệu> }`

```assembly
loop 4 {
  0x67  # Lặp lại việc chèn byte 0x67 bốn lần liên tiếp
}
hex 00 00  # Chèn thêm 2 byte 00 sau khi kết thúc vòng lặp

```

### 17. Ánh xạ phím bấm (Key Mapping cho fx-580VN X)

RAC cung cấp sẵn các hằng số ánh xạ phím (Keycodes). Người dùng có thể tra cứu toàn bộ danh sách mã phím đầy đủ tại tệp cấu hình tham chiếu `labels.txt`.

```assembly
KEY_SHIFT   # Đại diện cho mã quét phím SHIFT
KEY_1       # Đại diện cho mã quét phím số 1
KEY_ADD     # Đại diện cho mã quét phím cộng (+)

```

### 18. Hệ thống mở rộng cú pháp (Extension System)

RAC Compiler sở hữu kiến trúc mở (open-architecture) cho phép nhà phát triển tự định nghĩa các từ khóa, cú pháp mới hoặc macro tùy biến thông qua tệp cấu hình `extensions.txt`. Một khối định nghĩa extension gồm cấu trúc bắt buộc như sau:

* `---syntax---`: Khai báo cấu trúc cú pháp tùy biến và các tham số (đặt trong dấu ngoặc nhọn `{}`).
* `---output---`: Định dạng mã máy hoặc mã RAC tiêu chuẩn sẽ được sinh ra tương ứng để xử lý logic phần cứng.

**Ví dụ cấu hình trong `extensions.txt`:**

```text
---syntax---
render_bitmap({x},{y},{w},{h},{addr_bitmap})
---output---
xr0 = {x}, {y}, {w}, {h}
render_bitmap
er0 = {addr_bitmap}
---

```

---

## PHẦN V: PHỤ LỤC VÀ MÃ NGUỒN MẪU

### 19. Tích hợp Hàm Python (Python Inline Functions) — [ĐÃ BỊ LOẠI BỎ]

> ⚠️ **CẢNH BÁO THAY ĐỔI CÚ PHÁP:** Tính năng nhúng hàm xử lý bằng ngôn ngữ Python trực tiếp trong mã nguồn hiện **đã bị loại bỏ** khỏi các phiên bản mới của RAC Compiler. Mục này chỉ giữ lại để tham khảo lịch sử hệ thống.

```assembly
# Cú pháp cũ không còn hiệu lực:
def check_even_odd(n) {
  if n % 2 == 0:
    return 0x1
  else:
    return 0x0
}
py.check_even_odd(0x2)

```

### 20. Công cụ tìm kiếm Gadget (`find_gadgets`) — [ĐÃ BỊ LOẠI BỎ]

> ⚠️ **CẢNH BÁO THAY ĐỔI CÚ PHÁP:** Tính năng `find_gadgets` phục vụ cho kỹ thuật ROP (Return-Oriented Programming) hiện **đã bị loại bỏ** khỏi các phiên bản mới của RAC Compiler. Mục này chỉ giữ lại để tham khảo lịch sử phát triển của hệ thống.

```assembly
# Cú pháp cũ không còn hiệu lực:
find_gadgets {
  mov er{a[1]}, er{b[1]}
  pop pc
}
# Giải thích ký hiệu cũ:
# {var}    : Biến giả định nhận giá trị số từ 0 đến 15.
# {var[1]} : Biến giả định nhận giá trị số từ 0 đến 9.

```

### 21. Chương trình mẫu hoàn chỉnh (Complete Example)

Dưới đây là một chương trình RAC tiêu chuẩn kết hợp nhiều tính năng đã nêu, thực hiện cấu hình bộ nhớ, khai báo biến, định nghĩa chuỗi và thực thi gọi hàm hiển thị.

```assembly
org 0xe9e0                     # 1. Khai báo địa chỉ gốc chương trình tại 0xE9E0

var name = "Nguyen~Van~A"      # 2. Khai báo biến chuỗi (dùng '~' thay cho khoảng trắng)

lbl main                       # 3. Đặt nhãn bắt đầu chương trình chính
  "Hello,~{name}!"             # 4. Sử dụng String Interpolation để chèn tên vào chuỗi chào hỏi
  call print                   # 5. Gọi hàm 'print' hệ thống để xuất chuỗi ra màn hình hiển thị

```

> 💡 *Bạn có thể tham khảo thêm các ví dụ thực tế nâng cao tại thư mục cấu trúc nền tảng `rsc_ropchain/`.*

---

**Tác giả tài liệu:** `luongvantam`