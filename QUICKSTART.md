# 🚀 Quick Start Guide

## 1️⃣ Chuẩn Bị Môi Trường (5 phút)

### Windows

```bash
# Mở Command Prompt / PowerShell tại thư mục project

# Tạo virtual environment
python -m venv venv

# Kích hoạt environment
venv\Scripts\activate

# Cài đặt packages
pip install -r requirements.txt
```

### macOS / Linux

```bash
# Mở Terminal tại thư mục project

# Tạo virtual environment
python3 -m venv venv

# Kích hoạt environment
source venv/bin/activate

# Cài đặt packages
pip install -r requirements.txt
```

## 2️⃣ Tạo Sample Data (Optional)

```bash
python generate_sample_data.py
```

Lệnh này sẽ tạo folder `sample_data/` chứa file CSV mẫu để test.

## 3️⃣ Chạy Ứng Dụng

```bash
streamlit run app.py
```

✅ Ứng dụng sẽ tự động mở tại: `http://localhost:8501`

## 4️⃣ Sử Dụng Ứng Dụng

### Khi mới mở ứng dụng:

```
1. Trên thanh bên trái:
   - Kéo thả file T1 (quý trước)
   - Kéo thả file T2 (quý đối chiếu)

2. Nhấn nút "🔄 Xử Lý Đối Chiếu"

3. Chờ quá trình xử lý hoàn tất
```

### Sau khi xử lý thành công:

```
Bạn sẽ thấy 7 tab danh mục:
1. 📋 Chi Tiết Khách Hàng
2. 📊 Theo Chi Nhánh
3. 👥 Theo Phân Khúc
4. 📦 Theo Sản Phẩm
5. 🚨 Bất Thường
6. 📈 Biểu Đồ
7. 💾 Xuất Báo Cáo
```

## 5️⃣ Định Dạng File (Quan Trọng!)

### ✅ Tên File Đúng:

```
2600_dp01_20251231.csv
2602_dp01_20251231.csv
2604_dp01_20251231.csv
```

### ❌ Tên File Sai (Sẽ báo lỗi):

```
2600_dp01_2025-12-31.csv      (sai format ngày)
CN2600_dp01_20251231.csv      (sai format mã CN)
data_2600_20251231.csv        (thiếu _dp01_)
```

### ✅ Header (5 cột bắt buộc):

```csv
MA_KH,TEN_KH,DP_TYPE_CODE,CURRENT_BALANCE,CUST_TYPE_NAME
KH001,Công ty ABC,020,10000000,Doanh Nghiệp
KH002,Ông Trần Văn A,010,500000,Cá Nhân
```

### ❌ Header Sai (Sẽ báo lỗi):

```csv
MaKH,Name,Type,Balance,TypeName        (tên cột khác)
MA_KH,TEN_KH,DP_TYPE_CODE,CURRENT_BALANCE   (thiếu 1 cột)
MA_KH,TEN_KH,DP_TYPE_CODE,CURRENT_BALANCE,CUST_TYPE_NAME,EXTRA_COL  (cột thừa không sao, OK)
```

## 6️⃣ Mục Đích Của Mỗi Tab

### 📋 Chi Tiết Khách Hàng

- Xem từng khách hàng với chênh lệch riêng
- Lọc theo Chi Nhánh, Phân Khúc, Biến Động
- Đếm số khách: Mở Mới, Tất Toán, Tăng
- **Xuất Excel**: Tải dữ liệu đã lọc

### 📊 Theo Chi Nhánh

- Xem tổng hợp theo từng chi nhánh
- Tính % tăng trưởng (TY_LE_TANG_TRUONG)
- Sắp xếp theo DELTA cao nhất

### 👥 Theo Phân Khúc

- So sánh Cá Nhân vs Doanh Nghiệp
- Xem biểu đồ tương tác

### 📦 Theo Sản Phẩm

- Phân tích theo nhóm sản phẩm:
  - Tiết Kiệm
  - Có Kỳ Hạn
  - Không Kỳ Hạn

### 🚨 Bất Thường

- Khách hàng có DELTA lớn bất thường
- Top 20 khách hàng bất thường nhất
- Thống kê: Tăng bất thường, giảm bất thường

### 📈 Biểu Đồ

- 4 biểu đồ tương tác (Plotly)
- Có thể hover, zoom, download hình

### 💾 Xuất Báo Cáo

- Tải Excel với 5 sheet
- Tự động định dạng: tiền tệ, %
- File: `BaoCao_SoSanh_TienGui_YYYYMMDDhhmmss.xlsx`

## 7️⃣ Gặp Lỗi? Xử Lý Nhanh

| Lỗi                       | Giải Pháp                                                         |
| ------------------------- | ----------------------------------------------------------------- |
| "Tên file không hợp lệ"   | Kiểm tra format: `MACN_dp01_yyyymmdd.csv`                         |
| "Phải có cùng yyyymmdd"   | Tất cả file T1 phải cùng ngày, T2 phải cùng ngày                  |
| "Mã chi nhánh không khớp" | Thêm file thiếu cho cả 2 kỳ                                       |
| "Thiếu cột X"             | Thêm cột: MA_KH, TEN_KH, DP_TYPE, CURRENT_BALANCE, CUST_TYPE_NAME |
| Không load được CSV       | Lưu file dạng UTF-8 (.csv)                                        |

## 8️⃣ Mẹo Sử Dụng

✨ **Tip 1**: Khi xem "Chi Tiết Khách Hàng", lọc theo BIEN_DONG = "TAT_TOAN" để xem ai tất toán

✨ **Tip 2**: Xem tab "Bất Thường" để review khách lớn có biến động lạ

✨ **Tip 3**: Xuất Excel rồi gửi cho leader để report

✨ **Tip 4**: Dùng **Ctrl+F** (Cmd+F) trong tab để tìm khách hàng cụ thể

✨ **Tip 5**: Biểu đồ có thể double click để phóng to, click legend để ẩn/hiện

## 9️⃣ Dừng Ứng Dụng

```bash
# Trên terminal/console, nhấn:
Ctrl + C
```

## 🔟 Hủy Kích Hoạt Virtual Environment

```bash
# Windows
deactivate

# macOS/Linux
deactivate
```

---

**🎉 Hoàn thành! Bạn đã sẵn sàng sử dụng hệ thống.**

Có câu hỏi? Kiểm tra [README.md](README.md) để chi tiết hơn.
