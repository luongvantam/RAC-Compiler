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
2. Click the `...` (Views and More Actions) button at the top right of the Extensions view.
3. Select **Install from VSIX...**
4. Browse and select the `rsc.vsix` file included in this repository to install it.

#### 3. Running & Compiling Code

Depending on your host operating system platform, launch the dedicated automated script file located inside the compiler directory:

* **On Windows Platforms:** Double-click on `run.bat` (or execute via PowerShell/CMD environment).
* **On Linux / macOS Environments:** Launch terminal in the root directory path and execute `run.sh`:
```bash
chmod +x run.sh
./run.sh
```

* **Compilation Process:** 
  1. On first run, it will prompt you to enter the target calculator model (e.g., `580vnx`, `880btg`).
  2. At the main prompt, enter the exact source file name or full path to compile and press `Enter`.
  3. You can use the following interactive commands:
     - `!q`: Quit the compiler.
     - `!m`: Change the target model.
     - `!u`: Check for updates.


---

**Document Maintainer:** `luongvantam`