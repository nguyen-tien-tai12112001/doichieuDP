# 📘 Hướng Dẫn Chi Tiết - Hệ Thống So Sánh Dữ Liệu Tiền Gửi

## 🎯 Mục Đích Của Hệ Thống

Hệ thống này giúp bạn:

- ✅ So sánh dữ liệu tiền gửi giữa 2 quý (T1 và T2)
- ✅ Phát hiện khách hàng mới và khách tất toán
- ✅ Tính chênh lệch tiền gửi theo từng khách
- ✅ Phát hiện bất thường (outlier) trong dữ liệu
- ✅ Xuất báo cáo chuyên nghiệp dạng Excel

---

## 🚀 Hướng Dẫn Bắt Đầu (5 Bước)

### Bước 1: Chuẩn Bị Dữ Liệu

**Định dạng tên file:**

```
{MA_CN}_dp01_yyyymmdd.csv
```

**Ví dụ:**

- `2021_dp01_20231231.csv` → T1 quý trước
- `2021_dp01_20240331.csv` → T2 quý hiện tại

**Cơ Cấu Cột Bắt Buộc:**

```
MA_KH        → Mã khách hàng (không được trống)
TEN_KH       → Tên khách hàng
CUST_TYPE    → Phân khúc (0=Cá Nhân, 1=Pháp Nhân)
DP_TYPE_CODE → Loại sản phẩm (mã loại)
AMOUNT       → Số tiền gửi
```

**Lưu Ý:**

- File phải là CSV, encoding UTF-8
- Dữ liệu T1 và T2 phải có cùng cấu trúc
- Không được để trống cột MA_KH

### Bước 2: Tải File Lên

1. 📂 Kéo thả file T1 (quý trước) vào khung "Chọn file T1"
2. 📂 Kéo thả file T2 (quý đối chiếu) vào khung "Chọn file T2"
3. Bạn có thể chọn nhiều file nếu muốn xử lý nhiều chi nhánh cùng lúc

### Bước 3: Xử Lý Dữ Liệu

1. Bấm nút "🔄 Xử Lý Đối Chiếu" (nút màu xanh)
2. Hệ thống sẽ hiển thị thanh tiến độ:
   - 📁 Đang lưu tệp...
   - 🔍 Đang kiểm tra tệp...
   - ⚙️ Đang xử lý dữ liệu...
   - 💾 Đang chuẩn bị kết quả...

3. Chờ cho đến khi thấy ✅ "Hoàn tất!"

### Bước 4: Xem Kết Quả

Giao diện sẽ hiển thị:

- **📊 Tóm Tắt Nhanh** ở đầu: Các con số chính
- **7 Tab** để xem các báo cáo khác nhau:
  - 📋 Chi Tiết Khách Hàng
  - 📊 Theo Chi Nhánh
  - 👥 Theo Phân Khúc
  - 📦 Theo Sản Phẩm
  - 🚨 Bất Thường
  - 📈 Biểu Đồ
  - 💾 Xuất Báo Cáo

### Bước 5: Xuất Báo Cáo

1. Vào tab "💾 Xuất Báo Cáo"
2. Bấm "📥 Tải Xuống Excel Báo Cáo Đầy Đủ"
3. File Excel sẽ được tải về máy

---

## 📊 Giải Thích Chi Tiết Các Tab

### Tab 1: 📋 Chi Tiết Khách Hàng

**Hiển thị:**

- Danh sách tất cả khách hàng
- Dự tiền T1 (Quý Trước)
- Dự tiền T2 (Quý Hiện Tại)
- Chênh lệch (DELTA)
- Loại biến động

**Cách sử dụng:**

1. **Lọc dữ liệu:**
   - Chi Nhánh: Chọn chi nhánh cần xem
   - Phân Khúc: Cá Nhân hoặc Pháp Nhân
   - Biến Động: Mở Mới / Tăng / Giảm / Tất Toán / Không Đổi

2. **Xem thống kê nhanh:**
   - Tổng Khách Hàng
   - Mở Mới
   - Tất Toán
   - Tăng

3. **Xuất dữ liệu đã lọc:**
   - Bấm nút "📥 Xuất Excel (Dữ Liệu Đã Lọc)"
   - Chỉ xuất những khách hàng được lọc

**Ý Nghĩa Cột Biến Động:**

- **MO_MOI** 🆕: Khách hàng mới, chưa có dữ liệu T1
- **TAT_TOAN** 🔚: Khách đã đóng tài khoản, không có T2
- **TANG** 📈: Dư tiền tăng từ T1 sang T2
- **GIAM** 📉: Dư tiền giảm từ T1 sang T2
- **KHONG_DOI** ➡️: Dư tiền không thay đổi

### Tab 2: 📊 Theo Chi Nhánh

**Hiển thị:**

- Tổng dư tiền T1 của mỗi chi nhánh
- Tổng dư tiền T2 của mỗi chi nhánh
- Chênh lệch tổng
- Tỷ lệ tăng trưởng (%)

**Công thức:**

```
DELTA = TONG_T2 - TONG_T1
Tỷ Lệ Tăng Trưởng (%) = (TONG_DELTA / TONG_T1) × 100%
```

**Dùng để:** So sánh hiệu suất giữa các chi nhánh

### Tab 3: 👥 Theo Phân Khúc

**Hiển thị:**

- Thống kê riêng cho Cá Nhân
- Thống kê riêng cho Pháp Nhân
- So sánh giữa 2 phân khúc

**Dùng để:** Phân tích hành vi khách hàng theo từng nhóm

### Tab 4: 📦 Theo Sản Phẩm

**Hiển thị:**

- Thống kê theo loại sản phẩm
- Số khách hàng sử dụng mỗi sản phẩm
- Dư tiền theo sản phẩm
- Biểu đồ so sánh

**Dùng để:** Đánh giá hiệu suất từng sản phẩm

### Tab 5: 🚨 Bất Thường

**Bất Thường = Outlier:**
Các giao dịch có chênh lệch rất lớn so với trung bình, cần kiểm tra.

**Hệ thống sử dụng phương pháp IQR:**

```
IQR = Q3 - Q1 (Khoảng cách giữa 75% và 25%)
Outlier nếu: DELTA > Q3 + 1.5 × IQR
           hoặc DELTA < Q1 - 1.5 × IQR
```

**Dùng để:** Phát hiện giao dịch cần kiểm tra

### Tab 6: 📈 Biểu Đồ

**Hiển thị các biểu đồ tương tác:**

- Biểu đồ chiếu tiền T1 vs T2
- Biểu đồ biến động theo chi nhánh
- Biểu đồ phân phối khách hàng
- Biểu đồ theo phân khúc

**Lợi ích:**

- Dễ hình dung dữ liệu
- Có thể phóng to/thu nhỏ
- Có thể hover để xem giá trị chi tiết

### Tab 7: 💾 Xuất Báo Cáo

**Báo Cáo Excel bao gồm 5 Sheet:**

1. **Chi Tiết Khách Hàng** 📋
   - Danh sách tất cả khách
   - Để phân tích chi tiết

2. **Theo Chi Nhánh** 🏢
   - Thống kê tổng hợp theo chi nhánh
   - Để so sánh hiệu suất

3. **Theo Phân Khúc** 👥
   - Thống kê Cá Nhân vs Pháp Nhân
   - Để phân tích thị trường

4. **Theo Sản Phẩm** 📦
   - Thống kê theo loại sản phẩm
   - Để đánh giá sản phẩm

5. **Bất Thường** ⚠️
   - Danh sách outlier
   - Để kiểm tra giao dịch lạ

---

## 🎯 Các Chỉ Số Quan Trọng

### DELTA (Chênh Lệch)

```
DELTA = TONG_T2 - TONG_T1
```

- **DELTA > 0** ✅ : Tăng dư tiền
- **DELTA < 0** ❌ : Giảm dư tiền
- **DELTA = 0** ➡️ : Không thay đổi

### Tỷ Lệ Tăng Trưởng (TY_LE_TANG_TRUONG)

```
TY_LE_TANG_TRUONG (%) = (DELTA / TONG_T1) × 100%
```

- **> 0%** ✈️ : Tăng trưởng tích cực
- **< 0%** 📉 : Giảm
- **= 0%** ➡️ : Không thay đổi

### Outlier (Bất Thường)

Các giao dịch lớn hơn hoặc nhỏ hơn kỳ vọng nhiều.

Công thức IQR:

- Q1 = 25% percentile
- Q3 = 75% percentile
- IQR = Q3 - Q1
- **Outlier nếu:** |DELTA| > Q3 + 1.5 × IQR

---

## 💡 Mẹo & Thủ Thuật

### 1. Tìm Khách Hàng Mà Bạn Quan Tâm

- Vào Tab "Chi Tiết Khách Hàng"
- Lọc theo Chi Nhánh
- Lọc theo Biến Động = "MO_MOI" (khách mới)
- Xuất Excel để lưu trữ

### 2. So Sánh Hiệu Suất Chi Nhánh

- Vào Tab "Theo Chi Nhánh"
- Xem cột "TY_LE_TANG_TRUONG"
- Chi nhánh có % cao nhất là tốt nhất

### 3. Phát Hiện Giao Dịch Lạ

- Vào Tab "Bất Thường"
- Xem danh sách outlier
- Kiểm tra các khách hàng trong danh sách

### 4. Xuất Báo Cáo Cho Sếp

- Vào Tab "Xuất Báo Cáo"
- Bấm "Tải Xuống Excel"
- Mở file Excel có sẵn 5 sheet
- Có thể chỉnh sửa hoặc in trực tiếp

### 5. Xử Lý Lỗi

**Lỗi: "File không hoàn hãn"**

- Kiểm tra định dạng tên file: `{MA_CN}_dp01_yyyymmdd.csv`
- Kiểm tra file có cột MA_KH không

**Lỗi: "Dữ liệu T1 và T2 không khớp"**

- Kiểm tra cấu trúc cột giống nhau chưa
- Kiểm tra encoding file (phải UTF-8)

**Lỗi: "Không thể xuất báo cáo"**

- Kiểm tra bộ nhớ máy tính
- Thử xuất lại

---

## 📞 Hỗ Trợ

### Thông Tin Kỹ Thuật

- **Ngôn Ngữ:** Python
- **Framework:** Streamlit
- **Database:** CSV
- **Output:** Excel (XLSX)

### Liên Hệ

- Nếu gặp lỗi, hãy:
  1. Kiểm tra lại dữ liệu đầu vào
  2. Xem phần "Mẹo & Thủ Thuật" ở trên
  3. Tham khảo file này chương "Xử lý Lỗi"

---

## 📋 Bảng Tóm Tắt

| Tính Năng  | Mục Đích                    | Vị Trí         |
| ---------- | --------------------------- | -------------- |
| Tải File   | Nhập dữ liệu                | Thanh Bên Trái |
| Xử Lý      | Tính toán dữ liệu           | Thanh Bên Trái |
| Chi Tiết   | Xem từng khách              | Tab 1          |
| Chi Nhánh  | So sánh chi nhánh           | Tab 2          |
| Phân Khúc  | Phân tích Cá Nhân/Pháp Nhân | Tab 3          |
| Sản Phẩm   | Đánh giá sản phẩm           | Tab 4          |
| Bất Thường | Phát hiện outlier           | Tab 5          |
| Biểu Đồ    | Hình dung dữ liệu           | Tab 6          |
| Xuất Excel | Lưu báo cáo                 | Tab 7          |

---

**Chúc bạn sử dụng hệ thống thành công! 🎉**
