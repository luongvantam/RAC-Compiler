# RAC COMPILER

*Đọc bằng ngôn ngữ khác: [English](README.md), [中文](README.zh.md).*

---

## HƯỚNG DẪN TIẾNG VIỆT

### I. CÀI ĐẶT & KHỞI CHẠY (INSTALLATION & EXECUTION)

#### 1. Tải bộ biên dịch (Download)

Bạn có thể tải phiên bản mới nhất của RAC Compiler từ kho lưu trữ GitHub chính thức:

* **Repository Link:** [https://github.com/luongvantam/RAC-Compiler](https://github.com/luongvantam/RAC-Compiler)
* **Cách tải:** Chọn nút **Code** -> **Download ZIP** và giải nén, hoặc sử dụng lệnh Git:
```bash
git clone https://github.com/luongvantam/RAC-Compiler.git
```

#### 2. Cài đặt Tiện ích hiển thị cú pháp (Syntax Highlighting)

Để mã nguồn hiển thị trực quan và dễ đọc hơn trên Visual Studio Code:

1. Mở VS Code, nhấn tổ hợp phím `Ctrl + Shift + X` để vào mục Extensions.
2. Bấm vào biểu tượng dấu ba chấm `...` ở góc trên bên phải khung Extensions.
3. Chọn **Install from VSIX...**
4. Trỏ tới file `rsc.vsix` có sẵn trong thư mục dự án để cài đặt.

#### 3. Cách chạy chương trình và Biên dịch (Running & Compiling)

Tùy thuộc vào hệ điều hành, hãy khởi chạy file script khởi động trình biên dịch:

* **Trên Windows:** Click đúp vào file `run.bat` (hoặc mở Terminal/CMD gõ `run.bat`).
* **Trên Linux / macOS:** Mở Terminal tại thư mục gốc và thực thi file `run.sh`:
```bash
chmod +x run.sh
./run.sh
```

* **Quy trình biên dịch:** 
  1. Ở lần đầu chạy, hệ thống sẽ hỏi chọn model máy tính mục tiêu (ví dụ: `580vnx`, `880btg`).
  2. Tại màn hình chính, gõ đường dẫn hoặc tên file mã nguồn (ví dụ: `main.rsc`) và nhấn `Enter` để biên dịch.
  3. Bạn có thể sử dụng các lệnh đặc biệt sau trong dòng lệnh của compiler:
     - `!q`: Thoát trình biên dịch.
     - `!m`: Đổi sang model máy tính khác.
     - `!u`: Cập nhật (Update).

#### 4. Sử dụng IDE (Mới)

Dự án hiện có 2 môi trường phát triển tích hợp (IDE):

* **TUI IDE (Giao diện Terminal):**
  * Chạy `IDE.bat` trên Windows hoặc `./IDE.sh` trên Linux/macOS.
  * Hỗ trợ tô màu cú pháp trực tiếp trên Terminal.
  * Yêu cầu cài đặt module `textual` (tự động cài khi chạy script).

* **Web IDE (Giao diện Trình duyệt):**
  * Chạy `web.bat` trên Windows hoặc `./web.sh` trên Linux/macOS.
  * Mở trình duyệt và truy cập địa chỉ hiển thị trong terminal (thường là `http://localhost:8000`).

---

**Người bảo trì tài liệu:** `luongvantam`
