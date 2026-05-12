# 📤 Hướng Dẫn Deploy Lên GitHub & Streamlit Cloud

## 1️⃣ **Setup GitHub (Lần Đầu Tiên)**

### Bước 1: Chuẩn bị Project
```bash
# Tắt/loại bỏ các file không cần (data_warehouse/*.csv đã được loại bỏ bởi .gitignore)
# File cấu hình đã được cập nhật (.gitignore, config.toml)
```

### Bước 2: Khởi tạo Git Repository
```bash
cd d:\Code\ThiDuaKhenThuong
git init
git config user.name "Tên của bạn"
git config user.email "email@example.com"
git add .
git commit -m "Initial commit: Deposit comparison system"
```

### Bước 3: Tạo Repository trên GitHub
1. Vào https://github.com/new
2. Tạo repository mới (tên: `ThiDuaKhenThuong` hoặc tên khác)
3. **Chọn `Private`** (nếu dữ liệu nhạy cảm)
4. Copy lệnh từ "push an existing repository from the command line"

### Bước 4: Push lên GitHub
```bash
git remote add origin https://github.com/YOUR_USERNAME/ThiDuaKhenThuong.git
git branch -M main
git push -u origin main
```

---

## 2️⃣ **Cấu Hình Data Persistence cho Streamlit Cloud**

### ⚠️ **Vấn Đề**: Streamlit Cloud không lưu file tĩnh
- Mỗi lần deploy/refresh, file `*.db` và `data_warehouse/*.csv` bị xóa
- Cần dùng **Secrets** hoặc **Cloud Storage** để lưu dữ liệu

### 💡 **Giải Pháp**:

#### **Option A: Dùng Streamlit Secrets (Đơn Giản, Giới Hạn)**
```yaml
# .streamlit/secrets.toml (LOCAL ONLY - đừng push lên GitHub)
database_url = "sqlite:///data.db"
data_path = "/tmp/data_warehouse"
```

Cách dùng:
```python
import streamlit as st
db_url = st.secrets["database_url"]
```

#### **Option B: Dùng Google Cloud Storage (Khuyến Nghị)**

1. **Cài đặt Google Cloud**:
   ```bash
   pip install google-cloud-storage
   ```

2. **Tạo Cloud Storage Bucket** trên Google Cloud Console

3. **Tải dữ liệu lên Bucket**:
   ```python
   from google.cloud import storage
   
   def upload_database_to_gcs(local_db_path, bucket_name, blob_name):
       storage_client = storage.Client()
       bucket = storage_client.bucket(bucket_name)
       blob = bucket.blob(blob_name)
       blob.upload_from_filename(local_db_path)
   ```

4. **Tải dữ liệu từ Bucket**:
   ```python
   def download_database_from_gcs(bucket_name, blob_name, local_path):
       storage_client = storage.Client()
       bucket = storage_client.bucket(bucket_name)
       blob = bucket.blob(blob_name)
       blob.download_to_filename(local_path)
   ```

#### **Option C: Dùng SQLite + Auto-Backup (Đơn Giản Nhất)**

```python
# Trong app.py
import shutil
from pathlib import Path

def backup_database():
    """Sao lưu database sau mỗi thao tác quan trọng"""
    db_file = Path('app_database.db')
    if db_file.exists():
        backup_file = Path(f'backups/{db_file.stem}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db')
        backup_file.parent.mkdir(exist_ok=True)
        shutil.copy2(db_file, backup_file)
```

---

## 3️⃣ **Deploy Lên Streamlit Cloud**

### Bước 1: Đăng ký Streamlit Cloud
1. Vào https://streamlit.io/cloud
2. Đăng nhập bằng GitHub
3. Cho phép quyền truy cập repository

### Bước 2: Tạo Streamlit App
1. Click "New app"
2. Chọn repository `ThiDuaKhenThuong`
3. Branch: `main`
4. Main file path: `app.py`
5. Click "Deploy"

### Bước 3: Thiết lập Secrets (Nếu cần)
1. Vào **Settings** > **Secrets**
2. Dán nội dung `.streamlit/secrets.toml`:
   ```toml
   # Chỉ các config nhạy cảm
   database_password = "..."
   api_key = "..."
   ```

---

## 4️⃣ **Tối Ưu Cho Production**

### ✅ Checklist:
```
☐ Cập nhật requirements.txt (đã có)
☐ Thêm app.py, warehouse_ui.py vào repository
☐ Loại bỏ dữ liệu *.csv khỏi repo (.gitignore)
☐ Tạo README.md hướng dẫn sử dụng
☐ Cấu hình Secrets trên Streamlit Cloud
☐ Test deploy ở staging trước
☐ Bật HTTPS (tự động trên Streamlit Cloud)
☐ Thiết lập monitoring/logging
```

### 📝 File Cấu Hình Cần Có:
```
ThiDuaKhenThuong/
├── .gitignore          ✅ (đã update)
├── .streamlit/
│   ├── config.toml     ✅ (đã tạo)
│   └── secrets.toml    ⚠️ (LOCAL ONLY)
├── requirements.txt    ✅ (đã có)
├── app.py
├── warehouse_ui.py
└── data_warehouse/
    └── .gitkeep        ✅ (đã tạo)
```

---

## 5️⃣ **Giải Quyết Vấn Đề Dữ Liệu**

### 🔄 **Workflow Khuyến Nghị**:

```
Local Development:
├── Import CSV vào data_warehouse/
├── app_database.db được tạo
├── Test trên local: http://localhost:8501

Push lên GitHub:
├── *.csv được loại bỏ (gitignore)
├── Code được push
├── Commit history gọn nhẹ

Streamlit Cloud:
├── Clone code từ GitHub
├── Cài dependencies từ requirements.txt
├── Tạo empty data_warehouse/
├── User upload CSV trong app → lưu vào database
└── Database lưu trên storage (nếu cấu hình)
```

### 💾 **Cách Lưu Dữ Liệu Dài Hạn**:

```python
# Thêm vào app.py
import pickle
from pathlib import Path

def save_session_data():
    """Lưu dữ liệu session vào file"""
    if 'comparison_results' in st.session_state:
        with open('data_warehouse/session_backup.pickle', 'wb') as f:
            pickle.dump(st.session_state, f)

def load_session_data():
    """Tải dữ liệu từ file"""
    backup_file = Path('data_warehouse/session_backup.pickle')
    if backup_file.exists():
        with open(backup_file, 'rb') as f:
            return pickle.load(f)
    return None
```

---

## 6️⃣ **Các Lệnh Git Thường Dùng**

```bash
# Cập nhật code mới lên GitHub
git add .
git commit -m "Fix: Cải thiện tính năng XYZ"
git push origin main

# Kiểm tra trạng thái
git status
git log --oneline

# Xem những file bị loại bỏ
git check-ignore -v data_warehouse/*.csv
```

---

## ⚡ **Troubleshooting**

### Lỗi: "data_warehouse folder không tồn tại"
```python
from pathlib import Path
Path('data_warehouse').mkdir(exist_ok=True)
```

### Lỗi: Database bị xóa sau deploy
→ Dùng Option B (Google Cloud Storage) hoặc Option C (Auto-backup)

### Lỗi: File quá lớn để push
```bash
# Kiểm tra size
git ls-files -l | sort -rn | head -20

# Xóa khỏi git history (nếu đã push)
git rm --cached data_warehouse/*.csv
git commit -m "Remove large CSV files"
```

---

**🎉 Sau khi deploy, app sẽ chạy tại:**
```
https://your-username-thiduakhenhuong.streamlit.app
```
