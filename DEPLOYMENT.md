# 📦 Hướng Dẫn Đóng Gói & Chạy Offline

Hướng dẫn chi tiết để chạy dự án trên máy tính **không có kết nối Internet**.

---

## 🎯 Tổng Quan Quá Trình

```
Máy Tính 1 (Có Internet)          Máy Tính 2 (Không Có Internet)
    ↓                                    ↓
1. Tạo requirements.txt          1. Copy toàn bộ project
2. Tải tất cả packages           2. Cài đặt virtualenv
3. Đóng gói toàn bộ project      3. Cài đặt packages từ local
4. Chuyển sang USB/Disc          4. Chạy ứng dụng
```

---

## 📋 Chuẩn Bị Trên Máy Có Internet

### Bước 1: Cập Nhật Requirements

```bash
# 1.1 Vào thư mục project
cd D:\Code\ThiDuaKhenThuong

# 1.2 Kích hoạt virtual environment
venv\Scripts\activate

# 1.3 Cập nhật requirements.txt
pip freeze > requirements.txt
```

### Bước 2: Tải Tất Cả Packages Locally

```bash
# 2.1 Tạo thư mục chứa packages
mkdir wheels

# 2.2 Tải tất cả wheels (file .whl)
pip download -r requirements.txt -d wheels

# Hoặc download tất cả packages
pip download -r requirements.txt -d wheels --no-deps
```

**⚠️ Windows: Nếu bị lỗi `vswhere.exe ERROR`**

Pandas Python 3.13+ cần C++ build tools. Cài Visual Studio Build Tools:

```powershell
# Download (PowerShell Admin)
$url = "https://aka.ms/vs/17/release/vs_buildtools.exe"
$output = "$env:TEMP\vs_buildtools.exe"
Invoke-WebRequest -Uri $url -OutFile $output
& $output

# Trong installer: Chọn "Desktop development with C++" → Install
# Restart PowerShell khi xong
```

Hoặc download: [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)

**Kết quả:**

- Thư mục `wheels/` chứa tất cả file `.whl`
- Mỗi file là một dependency
- Có thể chuyển offline không cần internet

### Bước 3: Kiểm Tra File

```bash
# Kiểm tra danh sách packages
ls wheels/

# Kết quả tương tự:
# streamlit-1.28.0-py2.py3-none-any.whl
# pandas-2.1.0-cp313-cp313-win_amd64.whl
# ...vv...
```

### Bước 4: Tạo Script Setup

Tạo file `setup_offline.bat` (Windows):

```batch
@echo off
REM Tạo virtual environment
python -m venv venv

REM Kích hoạt venv
call venv\Scripts\activate.bat

REM Cài đặt packages từ thư mục wheels
pip install --no-index --find-links=wheels -r requirements.txt

REM In thông báo thành công
echo.
echo ✅ Cài đặt hoàn tất!
echo.
echo Để chạy app, gõ:
echo   venv\Scripts\activate
echo   streamlit run app.py
echo.
pause
```

Hoặc tạo file `setup_offline.sh` (Linux/Mac):

```bash
#!/bin/bash

# Tạo virtual environment
python3 -m venv venv

# Kích hoạt venv
source venv/bin/activate

# Cài đặt packages từ thư mục wheels
pip install --no-index --find-links=wheels -r requirements.txt

# In thông báo
echo ""
echo "✅ Cài đặt hoàn tất!"
echo ""
echo "Để chạy app, gõ:"
echo "  source venv/bin/activate"
echo "  streamlit run app.py"
echo ""
```

### Bước 5: Đóng Gói Project

```bash
# 5.1 Tạo thư mục gốc
mkdir ThiDuaKhenThuong_Offline
cd ThiDuaKhenThuong_Offline

# 5.2 Copy toàn bộ project
copy D:\Code\ThiDuaKhenThuong\* .

# 5.3 Cấu trúc thư mục cuối cùng
# ThiDuaKhenThuong_Offline/
# ├── app.py
# ├── validators.py
# ├── loader.py
# ├── aggregator.py
# ├── compare_engine.py
# ├── summary_engine.py
# ├── outlier_engine.py
# ├── exporter.py
# ├── generate_sample_data.py
# ├── requirements.txt
# ├── setup_offline.bat (hoặc .sh)
# ├── wheels/
# │   ├── streamlit-1.28.0-py2.py3-none-any.whl
# │   ├── pandas-2.1.0-cp313-cp313-win_amd64.whl
# │   └── ...
# ├── README.md
# ├── QUICKSTART.md
# ├── USER_GUIDE.md
# ├── FEATURES.md
# ├── CHANGELOG.md
# └── ...
```

### Bước 6: Nén & Chuyển File

```bash
# 6.1 Nén thư mục (Windows - dùng 7-Zip hoặc WinRAR)
# Hoặc dùng PowerShell:
Compress-Archive -Path ThiDuaKhenThuong_Offline -DestinationPath ThiDuaKhenThuong_Offline.zip

# 6.2 Kết quả: ThiDuaKhenThuong_Offline.zip (~500MB)

# 6.3 Chuyển file sang USB/Disc/Email
# - Copy file .zip sang USB
# - Hoặc chia nhỏ thành nhiều file nếu USB có giới hạn dung lượng
```

---

## 💻 Cài Đặt Trên Máy Không Có Internet

### Bước 1: Copy File

```bash
# 1.1 Copy file từ USB sang máy
# Ví dụ: D:\Projects\ThiDuaKhenThuong_Offline

# 1.2 Giải nén file zip (nếu đã nén)
# Click chuột phải → Extract All → OK
```

### Bước 2: Kiểm Tra Python

```bash
# 2.1 Mở Command Prompt (cmd) hoặc PowerShell

# 2.2 Kiểm tra Python đã cài chưa
python --version

# 2.3 Nếu chưa cài, cần cài Python trước (yêu cầu internet 1 lần)
# Hoặc copy Python từ máy khác
```

### Bước 3: Chạy Script Setup

**Windows:**

```bash
# 3.1 Vào thư mục project
cd D:\Projects\ThiDuaKhenThuong_Offline

# 3.2 Chạy script (double-click hoặc chạy từ cmd)
setup_offline.bat

# Hoặc chạy từ cmd:
cmd /c setup_offline.bat
```

**Linux/Mac:**

```bash
# 3.1 Vào thư mục project
cd /path/to/ThiDuaKhenThuong_Offline

# 3.2 Quyền thực thi
chmod +x setup_offline.sh

# 3.3 Chạy script
./setup_offline.sh
```

### Bước 4: Chạy Ứng Dụng

```bash
# 4.1 Kích hoạt virtual environment
# Windows:
venv\Scripts\activate

# Linux/Mac:
source venv/bin/activate

# 4.2 Chạy ứng dụng
streamlit run app.py

# 4.3 File sẽ hiển thị URL
# Local URL: http://localhost:8501
```

### Bước 5: Mở Ứng Dụng

- 🌐 Dùng trình duyệt: http://localhost:8501
- 📲 Hoặc copy URL vào trình duyệt
- ✅ Ứng dụng sẵn sàng sử dụng!

---

## 🔧 Xử Lý Lỗi Offline

### Lỗi 1: "Python not found"

```bash
# Cài đặt Python
# Tải từ python.org (yêu cầu internet)
# Hoặc copy từ máy khác có Python

# Kiểm tra Python
python --version
```

### Lỗi 2: "pip install failed"

```bash
# Kiểm tra thư mục wheels
ls wheels/

# Xác nhận file .whl đầy đủ
# Nếu thiếu, cần quay lại máy có internet để download

# Cài đặt lại
pip install --no-index --find-links=wheels -r requirements.txt
```

### Lỗi 3: "Module not found"

```bash
# Kiểm tra cài đặt
pip list

# Nếu vẫn thiếu, cài đặt thêm
pip install --no-index --find-links=wheels <package_name>
```

### Lỗi 4: "Port 8501 already in use"

```bash
# Dùng port khác
streamlit run app.py --server.port 8502

# Hoặc dừng process cũ trước
```

---

## 📊 Danh Sách Packages Quan Trọng

```
streamlit==1.28.0          # Web framework
pandas==2.1.0              # Data processing
plotly==6.6.0              # Interactive charts
openpyxl==3.1.2            # Excel export
numpy==1.24.0              # Numerical computing
scipy==1.10.0              # Scientific computing
```

**Tổng dung lượng:** ~500MB (bao gồm wheels)

---

## 📁 Cấu Trúc Thư Mục Hoàn Chỉnh

```
ThiDuaKhenThuong_Offline/
│
├── 📄 Core Files
│   ├── app.py                          # Main app
│   ├── validators.py                   # File validation
│   ├── loader.py                       # Data loading
│   ├── aggregator.py                   # Data aggregation
│   ├── compare_engine.py               # Comparison logic
│   ├── summary_engine.py               # Summary generation
│   ├── outlier_engine.py               # Outlier detection
│   ├── exporter.py                     # Excel export
│   └── generate_sample_data.py         # Sample data generator
│
├── 📚 Documentation
│   ├── README.md                       # Project overview
│   ├── QUICKSTART.md                   # Quick start guide
│   ├── USER_GUIDE.md                   # Detailed user guide
│   ├── FEATURES.md                     # Feature description
│   ├── CHANGELOG.md                    # Update history
│   └── DEPLOYMENT.md                   # This file
│
├── 🔧 Setup Files
│   ├── requirements.txt                # Python dependencies
│   ├── setup_offline.bat               # Windows setup script
│   ├── setup_offline.sh                # Linux/Mac setup script
│   └── wheels/                         # Downloaded packages
│       ├── streamlit-1.28.0-...whl
│       ├── pandas-2.1.0-...whl
│       ├── plotly-6.6.0-...whl
│       ├── openpyxl-3.1.2-...whl
│       ├── numpy-1.24.0-...whl
│       ├── scipy-1.10.0-...whl
│       └── ...vv...
│
└── 📂 Runtime (tự tạo khi chạy)
    ├── venv/                           # Virtual environment
    │   ├── Scripts/
    │   ├── Lib/
    │   └── ...
    └── .streamlit/                     # Streamlit config
```

---

## 🚀 Quick Start - Chạy Nhanh

### Máy Có Internet (Lần Đầu)

```bash
cd D:\Code\ThiDuaKhenThuong
pip freeze > requirements.txt
pip download -r requirements.txt -d wheels
# ... Tạo setup_offline.bat/sh ...
# ... Đóng gói thành .zip ...
```

**Kết quả:** File `ThiDuaKhenThuong_Offline.zip` (~500MB)

### Máy Không Internet

```bash
# 1. Extract file .zip
cd ThiDuaKhenThuong_Offline

# 2. Chạy setup (tùy hệ điều hành)
setup_offline.bat          # Windows
# hoặc
./setup_offline.sh         # Linux/Mac

# 3. Kích hoạt & chạy
venv\Scripts\activate      # Windows
streamlit run app.py

# 4. Mở http://localhost:8501
```

---

## 💡 Mẹo & Lưu Ý

### ✅ Nên Làm

- ✅ Kiểm tra Python version (3.8+)
- ✅ Đảm bảo wheels folder đầy đủ
- ✅ Backup requirements.txt
- ✅ Kiểm tra disk space (tối thiểu 1GB)
- ✅ Dùng USB 3.0 nếu có để chuyển nhanh

### ❌ Không Nên Làm

- ❌ Xóa thư mục wheels
- ❌ Sửa requirements.txt tùy tiện
- ❌ Chạy trên ổ C: (nếu không có quyền ghi)
- ❌ Di chuyển project khi đang chạy

---

## 🌐 Giải Pháp Thay Thế (Nếu Có Internet)

### Option 1: Cloud Deployment

```
Deploy lên Streamlit Cloud
→ Truy cập từ bất kỳ máy có internet
```

### Option 2: Docker Container

```
Tạo Docker image
→ Chạy từ máy bất kỳ
```

### Option 3: Executable (EXE)

```
Dùng PyInstaller để tạo .exe
→ Không cần Python
```

---

## 📞 Kiểm Tra & Debug

### Kiểm Tra Environments

```bash
# Liệt kê tất cả packages
pip list

# Kiểm tra phiên bản cụ thể
pip show streamlit

# Kiểm tra venv đang kích hoạt
which python
# hoặc (Windows)
where python
```

### Debug Mode

```bash
# Chạy với logging verbose
streamlit run app.py --logger.level=debug

# Kiểm tra file config
cat .streamlit/config.toml
```

---

## 📋 Checklist Trước Khi Chuyển

```
Máy Có Internet:
☑ Cập nhật requirements.txt
☑ Download tất cả wheels
☑ Tạo setup script
☑ Kiểm tra project chạy OK
☑ Nén & copy sang USB

Máy Không Internet:
☑ Copy file từ USB
☑ Cài Python (nếu chưa có)
☑ Chạy setup script
☑ Chạy streamlit run app.py
☑ Mở http://localhost:8501
```

---

**Chúc bạn cài đặt thành công! 🎉**

Nếu gặp vấn đề, kiểm tra phần "Xử Lý Lỗi Offline" ở trên.
