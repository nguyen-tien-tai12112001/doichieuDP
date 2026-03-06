# 📊 Hệ Thống So Sánh Dữ Liệu Tiền Gửi

Ứng dụng web nội bộ xây dựng bằng **Python + Streamlit** để so sánh dữ liệu tiền gửi giữa 2 quý (T1 và T2).

## 🎯 Chức Năng Chính

✅ So sánh dữ liệu tiền gửi giữa 2 quý  
✅ Tính chênh lệch theo từng khách hàng  
✅ Thống kê theo chi nhánh, phân khúc, nhóm sản phẩm  
✅ Phát hiện khách hàng mới / tất toán  
✅ Phát hiện bất thường (outlier) bằng IQR  
✅ Xuất báo cáo Excel với 5 sheet khác nhau  
✅ Biểu đồ tương tác với Plotly

## 📚 Hướng Dẫn

### 🎯 **[Chỉ Mục Tài Liệu (INDEX.md)](INDEX.md)** ← BẮT ĐẦU ĐỀ ĐÂY!

**Chọn hướng dẫn phù hợp:**

- 🚀 **[Bắt Đầu Nhanh](QUICKSTART.md)** (5 phút) - Cho người dùng mới
- 📖 **[Hướng Dẫn Người Dùng](USER_GUIDE.md)** (30 phút) - Chi tiết cách sử dụng
- 🌟 **[Chi Tiết Tính Năng](FEATURES.md)** - Mô tả kỹ thuật
- 📦 **[Chạy Offline - Nhanh](OFFLINE_QUICK.md)** (5 phút) - Chuẩn bị offline
- 🎯 **[Chạy Offline - Chi Tiết](DEPLOYMENT.md)** - Hướng dẫn đầy đủ
- 🔧 **[Đóng Gói Project](PACKAGING.md)** - Cách đóng gói

## 🛠️ Cài Đặt

### 1. Cài Đặt Môi Trường

```bash
# Tạo virtual environment
python -m venv venv

# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 2. Cài Đặt Packages

```bash
pip install -r requirements.txt
```

### 3. Chạy Ứng Dụng

```bash
streamlit run app.py
```

Ứng dụng sẽ mở tại: `http://localhost:8501`

## 📥 Định Dạng File Input

### Tên File (Format Bắt Buộc)

```
{MA_CN}_dp01_yyyymmdd.csv
```

**Ví dụ:**

```
2600_dp01_20251231.csv
2602_dp01_20251231.csv
2604_dp01_20251231.csv
```

### Header (Cột Bắt Buộc)

Mỗi file CSV phải có đúng các cột sau:

```
MA_KH              (string) - Mã khách hàng
TEN_KH             (string) - Tên khách hàng
DP_TYPE_CODE       (string) - Loại sản phẩm tiền gửi
CURRENT_BALANCE    (float)  - Số dư hiện tại
CUST_TYPE_NAME     (string) - Phân khúc khách hàng
```

### Ví Dụ Data

```
MA_KH,TEN_KH,DP_TYPE_CODE,CURRENT_BALANCE,CUST_TYPE_NAME
KH001,Công ty ABC,020,10000000.50,Doanh Nghiệp
KH002,Cá nhân XYZ,010,500000.00,Cá Nhân
KH003,Ngân Hàng XYZ,101,1000000.00,Doanh Nghiệp
```

## ⚙️ Quy Trình Xử Lý

### 1️⃣ Validation (Kiểm Tra)

- ✅ Tên file phải khớp format `MA_CN_dp01_yyyymmdd.csv`
- ✅ Tất cả file T1 phải có cùng `yyyymmdd`
- ✅ Tất cả file T2 phải có cùng `yyyymmdd`
- ✅ Mã chi nhánh (MA_CN) phải giống nhau giữa T1 và T2
- ✅ Mỗi file bắt buộc có 5 cột: MA_KH, TEN_KH, DP_TYPE, CURRENT_BALANCE, CUST_TYPE_NAME

### 2️⃣ Lọc Dữ Liệu

- Loại bỏ dòng có `DP_TYPE in ["401", "101"]`
- Chuẩn hoá kiểu dữ liệu (string, float)

### 3️⃣ Gộp Theo Khách Hàng

```
Group by: MA_KH, TEN_KH, CUST_TYPE_NAME
Tính: SUM(CURRENT_BALANCE)
```

### 4️⃣ Merge & Tính DELTA

```
Merge outer join T1 và T2 theo MA_KH
Fill NaN = 0
DELTA = TOTAL_T2 - TOTAL_T1
```

### 5️⃣ Phân Loại Biến Động

```
- MO_MOI:   T1 = 0 và T2 > 0  (khách hàng mới)
- TAT_TOAN: T1 > 0 và T2 = 0  (tất toán)
- TANG:     DELTA > 0          (tăng)
- GIAM:     DELTA < 0          (giảm)
- KHONG_DOI: DELTA = 0         (không thay đổi)
```

## 📊 Output

### Tab 1: Chi Tiết Khách Hàng

Bảng chi tiết với các cột:

```
MA_CN       - Mã chi nhánh
MA_KH       - Mã khách hàng
TEN_KH      - Tên khách hàng
CUST_TYPE_NAME - Phân khúc
TOTAL_T1    - Tổng dư T1
TOTAL_T2    - Tổng dư T2
DELTA       - Chênh lệch
BIEN_DONG   - Loại biến động
```

Cho phép lọc theo: Chi Nhánh, Phân Khúc, Biến Động

### Tab 2: Thống Kê Theo Chi Nhánh

```
MA_CN                  - Mã chi nhánh
TONG_T1               - Tổng T1
TONG_T2               - Tổng T2
TONG_DELTA            - Tổng chênh lệch
SO_KH                 - Số khách hàng
TY_LE_TANG_TRUONG     - % tăng trưởng
```

### Tab 3: Thống Kê Theo Phân Khúc

```
CUST_TYPE_NAME   - Phân khúc (Cá Nhân / Doanh Nghiệp)
TONG_T1          - Tổng T1
TONG_T2          - Tổng T2
TONG_DELTA       - Tổng chênh lệch
```

### Tab 4: Thống Kê Theo Nhóm Sản Phẩm

Mapping DP_TYPE → Nhóm:

```
TIET_KIEM    - Tiết kiệm (010, 011, 012)
CO_KY_HAN    - Có kỳ hạn (020, 021, 022, 050)
KHONG_KY_HAN - Không kỳ hạn (030, 031, 032, 040, 100, 102-119)
```

### Tab 5: Phát Hiện Bất Thường

Dùng phương pháp **IQR (Interquartile Range)**:

```
Bất thường = giá trị nằm ngoài [Q1 - 1.5*IQR, Q3 + 1.5*IQR]
```

Hiển thị: Top 50 khách hàng có DELTA bất thường nhất

### Tab 6: Biểu Đồ

4 biểu đồ tương tác:

1. **Bar Chart**: Tăng trưởng theo chi nhánh
2. **Pie Chart**: Tỷ lệ DELTA theo phân khúc
3. **Grouped Bar**: So sánh T1 vs T2 theo nhóm sản phẩm
4. **Bar Chart**: Phân bố biến động khách hàng

### Tab 7: Xuất Báo Cáo

Tải xuống file Excel với 5 sheet:

1. **Chi Tiết Khách Hàng** - Dữ liệu chi tiết tất cả khách hàng
2. **Theo Chi Nhánh** - Tổng hợp theo chi nhánh
3. **Theo Phân Khúc** - Tổng hợp theo phân khúc khách hàng
4. **Theo Sản Phẩm** - Tổng hợp theo nhóm sản phẩm
5. **Bất Thường** - Danh sách khách hàng bất thường

## 🏗️ Kiến Trúc Project

```
ThiDuaKhenThuong/
├── app.py                  # Streamlit UI chính
├── validators.py           # Kiểm tra file và header
├── loader.py              # Đọc và chuẩn hoá CSV
├── aggregator.py          # Group và tính tổng
├── compare_engine.py      # Merge và tính DELTA
├── summary_engine.py      # Thống kê theo CN, CUST_TYPE, DP_GROUP
├── outlier_engine.py      # Phát hiện bất thường
├── exporter.py            # Xuất Excel
├── requirements.txt        # Dependencies
└── README.md              # File hướng dẫn này
```

## 📦 Dependencies

```
streamlit==1.28.1          # UI Framework
pandas==2.1.0              # Data processing
plotly==5.17.0             # Interactive charts
openpyxl==3.11.0           # Excel export
numpy==1.24.3              # Numerical computing
scipy==1.11.2              # Outlier detection (Z-score)
```

## 🚀 Cách Sử Dụng

### Step 1: Chuẩn Bị File

1. Chuẩn bị file CSV theo format: `{MA_CN}_dp01_yyyymmdd.csv`
2. Đảm bảo có đủ 5 cột bắt buộc
3. Chuẩn bị 2 bộ file: T1 (quý trước) và T2 (quý đối chiếu)

### Step 2: Upload

1. Mở ứng dụng bằng `streamlit run app.py`
2. Kéo thả file T1 vào khu vực "T1 – Dữ Liệu Quý Trước"
3. Kéo thả file T2 vào khu vực "T2 – Dữ Liệu Quý Đối Chiếu"

### Step 3: Xử Lý

Nhấn nút **"🔄 Xử Lý Đối Chiếu"** - hệ thống sẽ:

- ✅ Kiểm tra tên file và header
- ✅ Kiểm tra mã chi nhánh khớp
- ✅ Xử lý dữ liệu
- ✅ Tính toán so sánh

### Step 4: Xem Kết Quả

- Xem chi tiết khách hàng
- Xem các thống kê theo khác nhau
- Phát hiện bất thường
- Xem biểu đồ tương tác

### Step 5: Xuất Báo Cáo

Nhấn **"📥 Tải Xuống Excel"** để tải file báo cáo

## 🔍 Các Lỗi Thường Gặp & Cách Khắc Phục

| Lỗi                                          | Nguyên Nhân              | Cách Khắc Phục                                                         |
| -------------------------------------------- | ------------------------ | ---------------------------------------------------------------------- |
| "Tên file không hợp lệ"                      | Format tên không đúng    | Kiểm tra format: `MACN_dp01_yyyymmdd.csv`                              |
| "Tất cả file trong T1 phải có cùng yyyymmdd" | File có ngày khác nhau   | Đảm bảo tất cả file T1 có cùng ngày                                    |
| "Mã chi nhánh không khớp"                    | T1 và T2 thiếu chi nhánh | Đảm bảo có file cho tất cả chi nhánh cả 2 kỳ                           |
| "File thiếu cột..."                          | File không có đủ 5 cột   | Thêm cột: MA_KH, TEN_KH, DP_TYPE_CODE, CURRENT_BALANCE, CUST_TYPE_NAME |
| Lỗi đọc file CSV                             | File bị lỗi encoding     | Lưu file dạng UTF-8                                                    |

## 💡 Tips

- 📌 Luôn kiểm tra định dạng tên file trước khi upload
- 📌 Sử dụng tab "Biểu Đồ" để visualize dữ liệu nhanh
- 📌 Kiểm tra tab "Bất Thường" để tìm khế hàng cần review
- 📌 Xuất Excel để gửi báo cáo cho lãnh đạo
- 📌 Có thể filter dữ liệu trên "Chi Tiết Khách Hàng" trước khi xem biểu đồ

## 📞 Support

Nếu gặp vấn đề:

1. Kiểm tra lại format file
2. Xem phần "Các Lỗi Thường Gặp"
3. Kiểm tra console Streamlit (terminal)

## 📝 License

Internal use only.

---

**Phiên bản:** 1.0  
**Ngày cập nhật:** 2024
