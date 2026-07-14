# HƯỚNG DẪN CÚ PHÁP RAC COMPILER

🇬🇧 [English](Guide.md) | 🌍 [中文](Guide.zh.md)

---

## 1. Ghi chú (Comments)
* **Cú pháp:**
  - `# <ghi_chú>`
  - `/* <ghi_chú_khối> */`

```assembly
# Ghi chú một dòng
/* 
   Ghi chú
   nhiều dòng 
*/
```

## 2. Biến số & Thanh ghi (Variables & Registers)
* **Cú pháp:**
  - `var <var> = <value>`
  - `reg <reg> = <value>`
  - `<reg> = <value>`
  - `<var> = <value>`
* **Gọi biến:**
  - `<name_var>` (ví dụ: `a`, `b`, `c`, `var`)

```assembly
var count = 10         # Khai báo biến count
reg r1 = 0x5           # Khởi tạo thanh ghi r1
r2 = 0xFF              # Gán trực tiếp giá trị cho r2
count = 20             # Gán lại giá trị cho biến count
count                  # Gọi/đánh giá biến count
```

## 3. Kiểu dữ liệu & Chuỗi ký tự (Data Types & Strings)
* **Cú pháp:**
  - Số nguyên / Hex: `<int(hex)>` (ví dụ: `0x02`, `10`) hoặc `hex <int(hex)>`
  - Chuỗi ký tự:
    - `"<chuỗi>"` (ký tự khoảng trắng thay bằng dấu ngã `~`, ví dụ: `"Xin~chào"`)
    - `"<chuỗi_f>"` (nội suy biến, ví dụ: `"hello {name}"`)
    - `'<chuỗi_token>'` (giữ nguyên cấu trúc phục vụ phân tích toán học/macro)
    - `str "<chuỗi>"` (biên dịch chuỗi thô)
    - `str <biến> "<chuỗi>"` (khai báo biến chuỗi)
    - `str <biến>` (gọi lại chuỗi thô của biến)
  - Mảng / Danh sách (Arrays):
    - `[<pt1>; <pt2>; ...]` (inline)
    - Khối nhiều dòng:
      ```assembly
      [
          <pt1>
          <pt2>
      ]
      ```
  - Đo lường bộ nhớ (Metrics):
    - `pr_length` / `sizeof()` (kích thước byte của phân vùng hiện tại)
    - `sizeof(<phân_vùng>)` (kích thước byte của phân vùng cụ thể)
    - `dist.<phân_vùng>` (khoảng cách byte giữa org và backup)
    - `pr_org(<phân_vùng>)` (địa chỉ gốc của phân vùng)
    - `pr_backup(<phân_vùng>)` (địa chỉ sao lưu của phân vùng)

```assembly
var ten = "World"
"Xin~chào,~{ten}!"        # Nội suy và đổi dấu ~ thành khoảng trắng
'sin( 9 0 )'              # Chuỗi token
str greeting "Hi"         # Khai báo biến chuỗi
str greeting              # Dịch chuỗi "Hi"
[0x1; 0x2]                # Mảng một dòng
[                         # Mảng nhiều dòng
  0x3
  0x4
]
var size = sizeof(main)
var delta = dist.launcher
```

## 4. Bí danh (Aliases)
* **Cú pháp:**
  - `<var/reg/gadget/label/...> as <tên_mới>`
  - `@section.<tên_cũ> [at <gốc> backup <sao_lưu>] as <tên_mới>`
  - `@set.<tên_cũ> [at <gốc> backup <sao_lưu>] as <tên_mới>`

```assembly
er0 as tmp
tmp = 0x12000                            # Dịch thành: er0 = 0x12

@section.init at 0x1000 backup 0x2000 as start
```

## 5. Nhãn & Lệnh Nhảy (Labels & Jump)
* **Cú pháp:**
  - Khai báo nhãn:
    - `lbl <label>`
    - `<label>:`
  - Lấy địa chỉ nhãn:
    - `adr(<label>)`
    - `adr(<label>, <offset>)`
    - `adr(<label>, <offset>, <base_addr>)`
    - `adr($)` (địa chỉ hiện tại của dòng này)
    - `adr_of <label>`
    - `adr_of [<offset>] <label>`
    - `adr_of [<offset>][<base_addr>] <label>`
  - Nhảy không điều kiện:
    - `goto <label>` (dịch thành: `er14 = adr(<label>, -2); sp = er14, pop er14`)

```assembly
lbl start
# hoặc:
start:
  goto end

lbl end
  var addr1 = adr(start)
  var addr2 = adr_of [-2][0x8000] end
```

## 6. Gọi chương trình & Gadget (Calls & Gadgets)
* **Cú pháp:**
  - `call <address/function_name>`
  - `def <gadget> : <address>` (thêm gadget vào command_dict)
  - `def {<tag>} <name_gadget>: <address>`

```assembly
def my_gadget : 0x17b34
call my_gadget
call 0x1234
def {memcpy} memcpy_auto_jmp: 0x12345
```

## 7. Ghép câu lệnh (Compound Statements)
* **Cú pháp:** `<câu_lệnh_1> ; <câu_lệnh_2> ; ...`

```assembly
call 0x1234 ; goto end
```

## 8. Macros động (Dynamic Macros)
* **Cú pháp:**
  - Dạng 1 dòng: `def <tên_macro>(<các_tham_số>) => <biểu_thức_1_dòng>`
  - Dạng khối lệnh: `def <tên_macro>(<các_tham_số>) => { <khối_lệnh> }`

```assembly
def add_hex(<val1>, <val2>) => eval(<val1> + <val2>)

def my_macro(<addr>, <val>) => {
    er0 = <addr>
    er2 = <val>
}
```

## 9. Hàm (Functions)
* **Cú pháp:**
  - Hàm nhiều dòng:
    ```assembly
    func <tên_hàm>(<các_tham_số>) {
        <code>
    }
    ```
  - Gọi hàm: `<tên_hàm>(<các_đối_số>)`
  - Hàm một dòng trả về (gán được cho biến/thanh ghi):
    `func <tên_hàm>(<các_tham_số>) { return <biểu_thức> }`

```assembly
func greet(person) {
  "Hello,~{person}!"
}
greet("Alice")

func add(x, y) { return x + y }
r1 = add(5, 10)
```

## 10. Chỉ thị vị trí nạp (`org` & `backup`)
* **Cú pháp:**
  - `org <addr_org>` (địa chỉ gốc nạp chương trình; bỏ qua nếu dùng `@set` inline `at`)
  - `backup <addr_backup>` (địa chỉ sao lưu vùng nhớ)

```assembly
org 0xe9e0
backup 0xd000
```

## 11. Phân vùng bộ nhớ (Sections)
* **Cú pháp:**
  - `@section.<tên> [at <địa_chỉ_gốc> backup <địa_chỉ_sao_lưu>]`
  - `@set.<tên> [at <địa_chỉ_gốc> backup <địa_chỉ_sao_lưu>]`

```assembly
@set.main at 0xe9e0 backup 0xf000
0x1234

@section.launcher at 0xd180
r1 = 0x5
```

## 12. Cấu hình Build (`@build`)
* **Cú pháp:**
  - Khối nhiều dòng:
    ```assembly
    @build {
        emu.inj = <true|false>
        emu.inj_file = "<file_name>"
        emu.inj_var = "<name_var>"
        emu.inj_adr[<section>] = <address>
        line.bytes = <count>
        output.file = <true|false>
        output.file_name = "<file_name>"
    }
    ```
  - Dòng đơn inline: `@build <key> = <value>; ...;`

```assembly
@build {
    emu.inj = true
    emu.inj_file = "payload.txt"
    emu.inj_var = "payload"
    line.gadgets = 0x30300000
    line.bytes = 16
    output.file = true
    output.file_name = "build_output.txt"
}
```

## 13. Phép toán thời gian biên dịch (Evaluation)
* **Cú pháp:**
  - `eval(<biểu_thức>)`
  - `calc(<biểu_thức>)`
  - `adr_arith <nhãn_1> <+/-> adr_arith <nhãn_2> ...`
  - `adr_arith [<offset_1>] <nhãn_1> <+/-> adr_arith [<offset_2>] <nhãn_2> ...`

```assembly
eval(0x1 + 0x2 * 0x3)                     # Kết quả: 0x7
calc(adr(label1) - adr(label2))
adr_arith start - adr_arith end
adr_arith [+4] start - adr_arith [-2] end
```

## 14. Vòng lặp & Đệm dữ liệu (Loops & Padding)
* **Vòng lặp:**
  - `loop <range> { <code> }`
  - `repeat <range> { <code> }`
* **Đệm dữ liệu (Padding):**
  - `fill(<count>, [<value>])`: Điền `<count>` byte với giá trị `<value>` (mặc định 0).
  - `align(<size>, [<value>])`: Điền byte đến khi địa chỉ chia hết cho `<size>`.
  - `pad(<offset>, [<value>])`: Điền byte đến khi kích thước phân vùng đạt `<offset>`.
  - `pad_abs(<address>, [<value>])`: Điền byte đến khi địa chỉ tuyệt đối đạt `<address>`.

```assembly
loop 4 {
  0x67
}

fill(16, 0xFF)
align(4)
pad(0x100, 0x00)
```

## 15. Khối lệnh Python nhúng (Embedded Python)
* **Cú pháp:** `@python { <mã_python> }`
* Chạy mã Python trực tiếp khi biên dịch. Có thể cấu hình biến thông qua `loader.vars_dict`.

```assembly
@python {
    # Tính toán phức tạp trong python
    loader.vars_dict["my_val"] = 0x1234 * 2
}
r1 = my_val
```

## 16. Ghép nối & Xuống dòng (Line Continuation)
* **Cú pháp:**
  - Dùng `\` ở cuối dòng để nối tiếp câu lệnh thô.
  - Các khối biểu thức `(...)`, `[...]` hoặc `{...}` tự động hỗ trợ viết trên nhiều dòng.

```assembly
hex 30 \
31

eval(
    0x01 + 0x02
)
```

---

**Tác giả tài liệu:** `luongvantam`