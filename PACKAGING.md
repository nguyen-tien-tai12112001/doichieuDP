# 📦 Hướng Dẫn Đóng Gói Project Chi Tiết

Hướng dẫn từng bước để chuẩn bị project chạy offline.

---

## 🎯 Mục Tiêu

Tạo một package hoàn chỉnh có thể chạy trên bất kỳ máy tính nào (kể cả không internet) với cùng kết quả.

**Điều kiện:**

- ✅ Python 3.8+ đã cài đặt
- ✅ Kết nối internet (để download packages)
- ✅ Storage ~1GB
- ✅ 15-30 phút

---

## 📋 Danh Sách Công Cụ Cần Có

### Bắt Buộc

- 🐍 Python 3.8+
- 📦 pip (thường có sẵn với Python)
- 💻 Command Line (cmd/PowerShell/bash)

### Lựa Chọn

- 📁 7-Zip hoặc WinRAR (để nén file)
- 💾 USB 3.0+ (để chuyển file nhanh)
- 🎯 Everything (Windows) để tìm file

---

## 🚀 Bước 1: Chuẩn Bị Môi Trường (10 phút)

### 1.1 Mở Command Line

**Windows:**

```
Win + R → Gõ cmd → Enter
```

**Linux/Mac:**

```
Ctrl + Alt + T (Linux)
Cmd + Space → Terminal (Mac)
```

### 1.2 Vào Thư Mục Project

```bash
# Windows
cd D:\Code\ThiDuaKhenThuong

# Linux/Mac
cd /path/to/ThiDuaKhenThuong
```

### 1.3 Kiểm Tra Python

```bash
python --version
# Hoặc (Linux/Mac)
python3 --version

# Kết quả: Python 3.x.x
```

### 1.4 Tạo Virtual Environment

```bash
# Windows & Linux/Mac
python -m venv venv

# Hoặc (Linux/Mac)
python3 -m venv venv
```

**Kết quả:** Thư mục `venv/` được tạo

### 1.5 Kích Hoạt Virtual Environment

**Windows:**

```batch
venv\Scripts\activate
```

**Linux/Mac:**

```bash
source venv/bin/activate
```

**Kiểm tra:** Command line prefix thay đổi thành `(venv) ...`

### 1.6 Cập Nhật pip

```bash
python -m pip install --upgrade pip
```

---

## 📥 Bước 2: Tạo Requirements File (2 phút)

### 2.1 Tạo File requirements.txt

```bash
# Đảm bảo đang ở thư mục project
pip freeze > requirements.txt
```

### 2.2 Kiểm Tra File

```bash
# Xem nội dung file
type requirements.txt    # Windows
cat requirements.txt     # Linux/Mac
```

**Kết quả tương tự:**

```
streamlit==1.28.0
pandas==2.1.0
plotly==6.6.0
openpyxl==3.1.2
numpy==1.24.0
scipy==1.10.0
...
```

---

## 📦 Bước 3: Tải Packages (5-10 phút)

### 3.1 Tạo Thư Mục wheels

```bash
mkdir wheels
REM hoặc (Linux/Mac): mkdir wheels
```

### 3.2 Download Tất Cả Packages

```bash
# Windows
pip download -r requirements.txt -d wheels

# Linux/Mac
python3 pip download -r requirements.txt -d wheels
```

**Thời gian:** 5-10 phút tùy tốc độ internet

### 3.3 Kiểm Tra Kết Quả

```bash
# Xem danh sách files
dir wheels          # Windows
ls wheels           # Linux/Mac
```

**Kết quả:** Danh sách files `.whl`

```
streamlit-1.28.0-py2.py3-none-any.whl
pandas-2.1.0-cp313-cp313-win_amd64.whl
plotly-6.6.0-py3-none-any.whl
...
```

---

## 📂 Bước 4: Chuẩn Bị File (5 phút)

### 4.1 Xóa Thư Mục venv (Không Cần)

```bash
# Windows (từ folder parent của project)
rmdir /s venv

# Linux/Mac
rm -rf venv
```

**Lý do:** venv khác nhau trên mỗi máy, sẽ tạo lại

### 4.2 Kiểm Tra Cấu Trúc Thư Mục

```
ThiDuaKhenThuong/
├── app.py
├── validators.py
├── loader.py
├── ... (các file .py khác)
├── requirements.txt
├── setup_offline.bat        ✅
├── setup_offline.sh         ✅
├── wheels/                  ✅
│   ├── streamlit-...whl
│   ├── pandas-...whl
│   └── ...
├── README.md
├── USER_GUIDE.md
├── DEPLOYMENT.md            ✅
└── ... (files tài liệu)
```

### 4.3 Kiểm Tra File Quan Trọng

```bash
# Windows
type requirements.txt
dir wheels | find ".whl"

# Linux/Mac
cat requirements.txt
ls wheels | grep .whl
```

---

## 🗜️ Bước 5: Nén Project (3-5 phút)

### Option A: Dùng PowerShell (Windows)

```powershell
# Windows PowerShell
Compress-Archive -Path ThiDuaKhenThuong -DestinationPath ThiDuaKhenThuong_Offline.zip

# Hoặc compress từ parent folder
cd ..
Compress-Archive -Path ThiDuaKhenThuong -DestinationPath ThiDuaKhenThuong_Offline.zip
```

### Option B: Dùng 7-Zip

```bash
# Windows
"C:\Program Files\7-Zip\7z.exe" a ThiDuaKhenThuong_Offline.zip ThiDuaKhenThuong

# Linux
7z a ThiDuaKhenThuong_Offline.zip ThiDuaKhenThuong
```

### Option C: WinRAR (GUI)

1. Click chuột phải thư mục project
2. Chọn "Add to archive..."
3. Đặt tên: `ThiDuaKhenThuong_Offline.zip`
4. Bấm OK

### Kiểm Tra File Zip

```bash
# Windows
dir | find ".zip"

# Linux/Mac
ls -lh *.zip
```

**Kích thước dự kiến:** 400-600 MB

---

## 💾 Bước 6: Sao Chép File (2-5 phút)

### 6.1 Sao Chép sang USB

```
Windows Explorer:
1. Mở Windows Explorer
2. Tìm file ThiDuaKhenThuong_Offline.zip
3. Copy (Ctrl+C)
4. Vào USB drive
5. Paste (Ctrl+V)
6. Đợi copy xong
```

### 6.2 Hoặc Upload Cloud

```
Google Drive/OneDrive:
1. Vào google.com/drive
2. Upload file .zip
3. Share link với ai cần
```

---

## ✅ Kiểm Tra Chi Tiết

### Checklist Trước Khi Chuyển

```
☐ File requirements.txt có nội dung
☐ Thư mục wheels chứa .whl files
☐ File setup_offline.bat/sh tồn tại
☐ Tất cả file .py nguồn có sẵn
☐ File tài liệu (.md) có sẵn
☐ File zip được tạo thành công
☐ File zip download/copy thành công
☐ Dung lượng file zip ~500MB
```

### Kiểm Tra Nội Dung Zip

```bash
# Windows (PowerShell)
Expand-Archive -Path ThiDuaKhenThuong_Offline.zip -Verbose | head -20

# Linux
unzip -l ThiDuaKhenThuong_Offline.zip | head -30
```

---

## 📊 Dung Lượng Referensi

| Thành Phần       | Dung Lượng  |
| ---------------- | ----------- |
| Project files    | ~10 MB      |
| wheels/ folder   | ~450-550 MB |
| requirements.txt | ~2 KB       |
| setup scripts    | ~10 KB      |
| **Total**        | **~500 MB** |

---

## 🚀 Lưu Ý Quan Trọng

### ✅ Nên Làm

- ✅ Test lại trên máy khác trước khi chuyển
- ✅ Kiểm tra tất cả file `.whl` tồn tại
- ✅ Backup requirements.txt
- ✅ Ghi chú Python version được dùng

### ❌ Không Nên Làm

- ❌ Không xóa thư mục wheels
- ❌ Không sửa requirements.txt
- ❌ Không di chuyển project khi venv đang kích hoạt
- ❌ Không nén riêng từng file

---

## 🔄 Quy Trình Hoàn Chỉnh (Tóm Tắt)

```
1. cd D:\Code\ThiDuaKhenThuong            (vào project)
2. python -m venv venv                     (tạo venv)
3. venv\Scripts\activate                   (kích hoạt)
4. pip freeze > requirements.txt           (tạo requirements)
5. mkdir wheels                            (tạo thư mục)
6. pip download -r requirements.txt -d wheels  (download)
7. rmdir /s venv                           (xóa venv)
8. Compress-Archive -Path ThiDuaKhenThuong -DestinationPath ThiDuaKhenThuong_Offline.zip
9. Copy .zip sang USB/Cloud
10. Done! ✅
```

---

## 🎯 Lệnh Nhanh (Copy-Paste)

### Windows (Chạy từ project folder)

```batch
python -m venv venv && ^
venv\Scripts\activate && ^
pip freeze > requirements.txt && ^
mkdir wheels && ^
pip download -r requirements.txt -d wheels && ^
echo ✅ Chuẩn bị xong! Giờ nén file.
```

### Linux/Mac

```bash
python3 -m venv venv && \
source venv/bin/activate && \
pip freeze > requirements.txt && \
mkdir wheels && \
pip download -r requirements.txt -d wheels && \
echo "✅ Chuẩn bị xong! Giờ nén file."
```

---

## 📞 Xử lý Lỗi Khi Đóng Gói

### "pip download" bị lỗi?

**Lỗi thường gặp:**

```
ERROR: vswhere.exe output
metadata-generation-failed: pandas
```

**Nguyên nhân:** Python 3.13+ cần C++ compiler để biên dịch pandas

**Giải pháp (Windows):**

```powershell
# 1. Cài Visual Studio Build Tools
# Download từ: https://aka.ms/vs/17/release/vs_buildtools.exe

# Hoặc chạy trong PowerShell (Admin):
$url = "https://aka.ms/vs/17/release/vs_buildtools.exe"
$output = "$env:TEMP\vs_buildtools.exe"
Invoke-WebRequest -Uri $url -OutFile $output
& $output

# 2. Trong installer:
#    - Chọn "Visual Studio Build Tools 2022"
#    - Checkmark "Desktop development with C++"
#    - Click Install (10-15 phút)
#    - Restart PowerShell

# 3. Thử lại
pip download -r requirements.txt -d wheels
```

**Giải pháp (Linux/Mac):**

```bash
# Ubuntu/Debian
sudo apt-get install build-essential python3-dev

# macOS
xcode-select --install
```

**Nếu vẫn lỗi:**

```bash
# Cập nhật pip trước
python -m pip install --upgrade pip

# Rồi thử lại
pip download -r requirements.txt -d wheels
```

### Dung lượng không đủ?

```bash
# Kiểm tra dung lượng disk
# Windows: Clicc chuột phải ổ C: → Properties
# Linux: df -h
# Mac: Sistem Preferences → Storage

# Nếu không đủ, xóa những file không cần (temp, cache)
```

### Thư mục wheels bị lỗi khi nén?

```bash
# Xóa wheels cũ
rmdir /s wheels    # Windows
rm -rf wheels      # Linux/Mac

# Tạo lại
mkdir wheels
pip download -r requirements.txt -d wheels
```

---

**Chúc bạn chuẩn bị thành công! 🎉**

Sau khi chuẩn bị xong, hãy chạy `setup_offline.bat/sh` trên máy không internet.
