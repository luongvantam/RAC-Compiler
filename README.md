# RAC COMPILER

🌐 **Language / Ngôn ngữ:**

* **Tiếng Việt:** Cuộn xuống [Phần A: Hướng dẫn Tiếng Việt](https://www.google.com/search?q=%23phan-a-huong-dan-tieng-viet).
* **English:** Scroll down to [Section B: English Guide](https://www.google.com/search?q=%23section-b-english-guide).

---

## PHẦN A: HƯỚNG DẪN TIẾNG VIỆT

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
2. Tìm kiếm từ khóa: `"RSC Syntax Highlight"`.
3. Nhấn **Install** để cài đặt.

#### 3. Cách chạy chương trình và Biên dịch (Running & Compiling)

Tùy thuộc vào hệ điều hành bạn đang sử dụng, hãy khởi chạy file script tương ứng trong thư mục:

* **Trên Windows:** Click đúp vào file `launcher580.bat` (hoặc chạy qua Terminal).
* **Trên Linux / macOS:** Mở Terminal tại thư mục gốc và thực thi file `run580.sh`:
```bash
chmod +x run580.sh
./run580.sh

```


* **Quy trình biên dịch:** Sau khi giao diện dòng lệnh hiện lên, hệ thống sẽ yêu cầu bạn **nhập tên file muốn dịch** (ví dụ: `main.rsc`). Hãy nhập chính xác tên file (không nhập đuôi file) và nhấn `Enter` để trình biên dịch bắt đầu xử lý và xuất file mã máy cuối cùng.

---

## SECTION B: ENGLISH GUIDE

### I. INSTALLATION & EXECUTION

#### 1. Download the Compiler

Get the latest source code and distribution releases from the official GitHub repository:

* **Repository Link:** [https://github.com/luongvantam/RAC-Compiler](https://github.com/luongvantam/RAC-Compiler)
* **Method:** Click the **Code** button -> **Download ZIP** and extract it, or execute via Git terminal clone:
```bash
git clone https://github.com/luongvantam/RAC-Compiler.git

```



#### 2. Syntax Highlighting Support

To secure code visual enhancement when coding on Visual Studio Code:

1. Open VS Code and open the Extension tab using `Ctrl + Shift + X` (or `Cmd + Shift + X` on macOS).
2. Search for the marketplace identifier keyword: `"RSC Syntax Highlight"`.
3. Click **Install**.

#### 3. Running & Compiling Code

Depending on your host operating system platform, launch the dedicated automated script file located inside the compiler directory:

* **On Windows Platforms:** Double-click on `launcher580.bat` (or execute via PowerShell/CMD environment).
* **On Linux / macOS Environments:** Launch terminal in the root directory path and execute `run580.sh`:
```bash
chmod +x run580.sh
./run580.sh

```


* **Compilation Process:** When the command line prompt initializes, the script will request you to **enter the input file name you want to compile** (e.g., `main.rsc`). Type the exact source file name explicitly and press `Enter` to run the processor layout compilation block (Do not include .rsc in the file name).


---

**Document Maintainer:** `luongvantam`