# 🎬 Quick Start - Đóng Gói & Chạy Offline (5 Phút)

## 🔥 Cách Nhanh Nhất

### Bước 1: Máy Có Internet (10 phút)

```bash
# 1.1 Vào project
cd D:\Code\ThiDuaKhenThuong

# 1.2 Tạo venv
python -m venv venv

# 1.3 Kích hoạt
venv\Scripts\activate

# (hoặc Linux/Mac: source venv/bin/activate)

# 1.4 Tạo requirements
pip freeze > requirements.txt

# 1.5 Tạo wheels folder
mkdir wheels

# 1.6 Download packages
pip download -r requirements.txt -d wheels

# 1.7 Xóa venv (không cần cho offline)
rmdir /s venv
```

### Bước 2: Nén & Copy (5 phút)

```bash
# Windows PowerShell: Nén project
Compress-Archive -Path ThiDuaKhenThuong -DestinationPath ThiDuaKhenThuong_Offline.zip

# Hoặc dùng 7-Zip/WinRAR (GUI)
# Copy file .zip sang USB
```

### Bước 3: Máy Không Internet (2 phút)

```bash
# 3.1 Extract .zip
# Click chuột phải → Extract

# 3.2 Vào project
cd ThiDuaKhenThuong_Offline

# 3.3 Chạy setup (Windows)
setup_offline.bat

# (hoặc Linux/Mac: chmod +x setup_offline.sh && ./setup_offline.sh)
```

### Bước 4: Chạy App (1 phút)

```bash
# 4.1 Kích hoạt venv
venv\Scripts\activate
# (hoặc: source venv/bin/activate)

# 4.2 Chạy app
streamlit run app.py

# 4.3 Trình duyệt tự mở hoặc vào
# http://localhost:8501
```

---

## 📋 Danh Sách File Cần Có

```
ThiDuaKhenThuong_Offline/
├── ✅ app.py
├── ✅ validators.py (và các module khác)
├── ✅ requirements.txt
├── ✅ setup_offline.bat
├── ✅ setup_offline.sh
├── ✅ wheels/          (thư mục packages)
├── ✅ README.md
└── ✅ USER_GUIDE.md
```

---

## 🎯 Tóm Tắt 3 Bước

| Bước | Hành Động         | Thời Gian | Yêu Cầu        |
| ---- | ----------------- | --------- | -------------- |
| 1    | Download packages | 10 phút   | Internet       |
| 2    | Nén & copy        | 5 phút    | USB/Cloud      |
| 3    | Setup & chạy      | 2 phút    | Không internet |

---

## ⚡ Copy-Paste Nhanh

### Windows (Một lệnh chạy tất cả)

```powershell
# Chạy lần 1 (có internet)
python -m venv venv; .\venv\Scripts\activate; pip freeze > requirements.txt; mkdir wheels; pip download -r requirements.txt -d wheels; rm -r venv

# Kết quả: ThiDuaKhenThuong_Offline.zip (~500MB)
```

### Linux/Mac (Một lệnh)

```bash
# Chạy lần 1 (có internet)
python3 -m venv venv && source venv/bin/activate && pip freeze > requirements.txt && mkdir wheels && pip download -r requirements.txt -d wheels && rm -rf venv

# Kết quả: ThiDuaKhenThuong_Offline.zip (~500MB)
```

---

## ✅ Checklist

```
Máy Có Internet:
☐ Download packages xong
☐ Nén thành .zip
☐ Copy sang USB

Máy Không Internet:
☐ Extract .zip
☐ Chạy setup_offline.bat/sh
☐ Chạy streamlit run app.py
☐ Truy cập http://pip install dask==2023.12.1 scikit-learn==1.3.0:8501
```

---

## 🚫 Lỗi Phổ Biến & Cách Sửa

| Lỗi                                   | Giải Pháp                                                                                  |
| ------------------------------------- | ------------------------------------------------------------------------------------------ |
| `ModuleNotFoundError`                 | Chạy `setup_offline.bat/sh` lại                                                            |
| `Port already in use`                 | Dùng port khác: `streamlit run app.py --server.port 8502`                                  |
| `wheels folder empty`                 | Chạy `pip download -r requirements.txt -d wheels`                                          |
| `Python not found`                    | Cài Python (yêu cầu internet 1 lần)                                                        |
| `vswhere.exe output ERROR`            | **Windows Build Tools missing!** Cài Visual Studio C++ Build Tools (xem mục "Build Tools") |
| `metadata-generation-failed` (pandas) | Cài **Microsoft C++ Build Tools** - xem "⚙️ Windows Build Tools Setup"                     |

---

## ⚙️ Windows Build Tools Setup

**Vấn Đề:** Python 3.13+ cần biên dịch pandas từ source, cần C++ compiler

**Giải Pháp:**

```powershell
# 1. Download installer (trong PowerShell Admin)
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

**Hoặc download tập build tools này: [Build Tools Installer](https://visualstudio.microsoft.com/visual-cpp-build-tools/)**

---

## 🎉 Done!

Ứng dụng sẵn sàng chạy offline! 🚀

**Mỗi lần sử dụng:**

```bash
venv\Scripts\activate
streamlit run app.py
```

---

**Cần chi tiết hơn? Xem [DEPLOYMENT.md](DEPLOYMENT.md) hoặc [PACKAGING.md](PACKAGING.md)**
