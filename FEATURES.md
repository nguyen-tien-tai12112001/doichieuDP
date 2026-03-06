# 🌟 Các Tính Năng Chi Tiết

## 📊 Tính Năng Chính

### 1. 📥 Tải & Xác Thực Dữ Liệu

**Chức Năng:**

- Tải nhiều file CSV cùng lúc
- Xác minh định dạng tên file
- Kiểm tra cấu trúc cột
- Hỗ trợ UTF-8 encoding

**Quá Trình:**

```
Tải File → Kiểm Tra Tên → Kiểm Tra Cột → Lưu Tệp Tạm
```

**Lợi Ích:**

- Phát hiện lỗi sớm
- Tránh xử lý dữ liệu sai

---

### 2. 🔄 Xử Lý Dữ Liệu

**Các Bước:**

1. **Chuẩn Hóa** (Normalize)
   - Chuyển đổi kiểu dữ liệu
   - Loại bỏ dữ liệu trống
   - Tinh chỉnh format số

2. **Lọc** (Filter)
   - Loại bỏ dòng không hợp lệ
   - Giữ lại dữ liệu sạch

3. **Tổng Hợp** (Aggregate)
   - Tính tổng tiền theo khách hàng
   - Nhóm theo sản phẩm

4. **So Sánh** (Compare)
   - Ghép T1 và T2
   - Tính DELTA
   - Phân loại biến động

---

### 3. 📈 Phân Tích Dữ Liệu

#### A. Thống Kê Theo Chi Nhánh

```
TÓM TẮT:
├─ Tổng T1 (quý trước)
├─ Tổng T2 (quý hiện tại)
├─ Chênh Lệch (DELTA)
└─ Tỷ Lệ Tăng Trưởng (%)
```

#### B. Phân Tích Theo Phân Khúc

```
PHÂN KHÚC:
├─ Cá Nhân
│  ├─ Số lượng KH
│  ├─ Tổng tiền
│  └─ Chênh lệch
└─ Pháp Nhân
   ├─ Số lượng KH
   ├─ Tổng tiền
   └─ Chênh lệch
```

#### C. Đánh Giá Theo Sản Phẩm

```
SẢN PHẨM:
├─ Mỗi loại sản phẩm
│  ├─ Số khách sử dụng
│  ├─ Tổng tiền
│  └─ Biến động
```

#### D. Phân Loại Biến Động

```
BIEN_DONG:
├─ MO_MOI: Khách mới
├─ TAT_TOAN: Khách đóng
├─ TANG: Tăng tiền
├─ GIAM: Giảm tiền
└─ KHONG_DOI: Không đổi
```

---

### 4. 🚨 Phát Hiện Bất Thường (Outlier Detection)

**Phương Pháp: IQR (Interquartile Range)**

```
Bước 1: Tính Q1 (25% percentile)
Bước 2: Tính Q3 (75% percentile)
Bước 3: IQR = Q3 - Q1
Bước 4: Ngưỡng thấp = Q1 - 1.5 × IQR
Bước 5: Ngưỡng cao = Q3 + 1.5 × IQR
Bước 6: Outlier nếu DELTA < ngưỡng thấp HOẶC > ngưỡng cao
```

**Ích Lợi:**

- Tự động phát hiện giao dịch lạ
- Không cần cài đặt thủ công
- Khoa học và thống kê

---

### 5. 📊 Biểu Đồ Tương Tác

**Loại Biểu Đồ:**

- 📊 Bar Chart: So sánh giữa các nhóm
- 📈 Line Chart: Xu hướng theo thời gian
- 🥧 Pie Chart: Tỷ lệ phân phối
- 📌 Scatter Plot: Mối quan hệ

**Tính Năng:**

- Phóng to/thu nhỏ
- Hover để xem chi tiết
- Export thành hình ảnh
- Tương tác động

---

### 6. 💾 Xuất Báo Cáo Excel

**File Bao Gồm 5 Sheet:**

| Sheet       | Nội Dung                | Dạng    |
| ----------- | ----------------------- | ------- |
| Chi Tiết KH | Danh sách tất cả khách  | Bảng    |
| Chi Nhánh   | Thống kê theo chi nhánh | Tóm tắt |
| Phân Khúc   | Cá Nhân vs Pháp Nhân    | Tóm tắt |
| Sản Phẩm    | Theo loại sản phẩm      | Tóm tắt |
| Bất Thường  | Danh sách outlier       | Bảng    |

**Định Dạng:**

- Header màu xanh nước biển
- Font chữ in đậm
- Số tiền định dạng tiền tệ
- Có đường viền

**Tính Năng:**

- Có thể mở với Excel, Google Sheets
- Có thể chỉnh sửa tiếp
- Có thể in trực tiếp
- Có thể chia sẻ

---

## 🎨 Giao Diện

### Bố Cục

```
┌─────────────────────────────────────────────┐
│              HEADER                         │
│     📊 Hệ Thống So Sánh Dữ Liệu Tiền Gửi  │
└─────────────────────────────────────────────┘

┌─────────────┐  ┌──────────────────────────┐
│   SIDEBAR   │  │    MAIN CONTENT          │
│             │  │                          │
│ Upload      │  │  Tóm Tắt Nhanh           │
│ Hướng Dẫn   │  │  📈 Các Tab              │
│ Mẹo        │  │  📊 Dữ Liệu              │
│             │  │  📉 Biểu Đồ              │
└─────────────┘  └──────────────────────────┘
```

### Sidebar (Thanh Bên Trái)

- 📖 Hướng Dẫn Sử Dụng (có thể mở rộng)
- 📋 Phần Tải Tệp
- 🔄 Nút Xử Lý
- 💡 Mẹo & Thông Tin

### Main Content (Nội Dung Chính)

- 📊 Tóm Tắt Nhanh (5 metrics)
- 7 Tab chứa các báo cáo khác nhau
- Có thể lọc, tìm, xuất

---

## ⚡ Performance

### Tối ưu Hóa Tốc Độ

**Excel Export:**

- Giảm styling phức tạp
- Dùng openpyxl tối ưu
- Đồng bộ hóa dữ liệu

**Data Processing:**

- Dùng Pandas vectorization
- Tránh loop
- Cache dữ liệu

**UI Rendering:**

- Lazy loading
- Caching results
- Efficient re-rendering

---

## 🔒 Bảo Mật & Quyền Riêng Tư

### Bảo Mật Dữ Liệu

- ✅ Dữ liệu lưu trong thư mục tạm
- ✅ Tự động xóa sau khi tắt app
- ✅ Không lưu trên server
- ✅ Không gửi dữ liệu ra ngoài

### Hỗ Trợ Format

- ✅ CSV (UTF-8)
- ✅ Excel
- ✅ Các format khác (có thể mở rộng)

---

## 🔧 Cấu Hình

### Thông Số Mặc Định

```python
# IQR Outlier Detection
OUTLIER_IQR_MULTIPLIER = 1.5

# Excel Export
EXCEL_SHEET_NAMES = [
    'Chi Tiết Khách Hàng',
    'Theo Chi Nhánh',
    'Theo Phân Khúc',
    'Theo Sản Phẩm',
    'Bất Thường'
]

# UI
PAGE_LAYOUT = "wide"
INITIAL_SIDEBAR = "expanded"
```

### Có Thể Tùy Chỉnh

- Output format
- Ngưỡng outlier
- Tên sheet
- Styling

---

## 📋 Cột Dữ Liệu

### Cột Đầu Vào (Input)

```
MA_KH         → Mã khách (bắt buộc)
TEN_KH        → Tên khách
CUST_TYPE     → Phân khúc
DP_TYPE_CODE  → Loại sản phẩm
AMOUNT        → Số tiền
```

### Cột Đầu Ra (Output)

```
MA_CN         → Mã chi nhánh
MA_KH         → Mã khách
TEN_KH        → Tên khách
CUST_TYPE_NAME → Tên phân khúc
TOTAL_T1      → Tổng T1
TOTAL_T2      → Tổng T2
DELTA         → Chênh lệch
BIEN_DONG     → Loại biến động
DP_TYPE_NAME  → Tên sản phẩm
```

---

## 🌐 Công Nghệ Sử Dụng

### Backend

- Python 3.13
- Pandas (xử lý dữ liệu)
- NumPy (tính toán)
- SciPy (thống kê)

### Frontend

- Streamlit (giao diện)
- Plotly (biểu đồ)
- HTML/CSS (styling)

### Storage

- CSV (input)
- Excel (output)
- Temp files (xử lý)

---

## 🚀 Tính Năng Nâng Cao

### Có Thể Thêm:

- 🔐 Đăng nhập & phân quyền
- 💾 Database integration
- 📅 Lịch sử báo cáo
- 📧 Gửi báo cáo qua email
- 📱 Responsive mobile
- 🌙 Dark mode
- 🔔 Thông báo alert
- 📊 Dashboard tương tác

---

**Tất cả các tính năng được thiết kế để dễ sử dụng và hiệu quả! 🎯**
