# 📘 Hướng Dẫn Chi Tiết - Hệ Thống So Sánh Dữ Liệu Tiền Gửi

## 🎯 Mục Đích Của Ứng Dụng

Ứng dụng giúp bạn:

- ✅ So sánh dữ liệu tiền gửi giữa 2 kỳ (T1 và T2)
- ✅ Phát hiện khách hàng mới, khách tất toán, khách tăng/giảm
- ✅ Xây dựng báo cáo Excel chuyên nghiệp
- ✅ Phát hiện bất thường giao dịch bằng IQR
- ✅ Kiểm tra lịch sử xử lý và phục hồi kết quả cũ
- ✅ Dự báo động thái chi nhánh và gợi ý hành động
- ✅ Có thể ghi dữ liệu kết quả vào MariaDB

---

## 🚀 Hướng Dẫn Sử Dụng

### Bước 1: Chuẩn Bị Dữ Liệu

**Định dạng tên file:**

```
{MA_CN}_dp01_yyyymmdd.csv
```

**Ví dụ:**

- `2021_dp01_20231231.csv` → file T1 quý trước
- `2021_dp01_20240331.csv` → file T2 quý đối chiếu

**Cột bắt buộc:**

- `MA_KH` — Mã khách hàng
- `TEN_KH` — Tên khách hàng
- `DP_TYPE_CODE` — Mã loại sản phẩm
- `CURRENT_BALANCE` — Số dư hiện tại
- `CUST_TYPE_NAME` — Phân khúc khách hàng

**Ghi chú:**

- File phải là CSV
- Nếu tên cột nguồn khác, dùng phần "Mapping Cột" để đổi tên về chuẩn
- T1 và T2 phải cùng cấu trúc cột

### Bước 2: Upload Dữ Liệu

1. Mở Sidebar
2. Trong phần `Upload dữ liệu`:
   - Chọn file T1 (nhiều file được phép)
   - Chọn file T2 (nhiều file được phép)
3. Kiểm tra thông báo số file đã load lên

### Bước 3: Validate dữ liệu

1. Mở phần `Mapping Cột` để kiểm tra nếu cần đổi tên cột
2. Bấm `2️⃣ Kiểm tra dữ liệu`
3. Ứng dụng sẽ kiểm tra:
   - tên file đúng định dạng
   - dữ liệu đầy đủ cho mỗi chi nhánh
   - cột bắt buộc đã xuất hiện

### Bước 4: So sánh dữ liệu

1. Bấm `3️⃣ So sánh dữ liệu`
2. Chờ thanh tiến độ hoàn thành
3. Nếu ứng dụng báo thành công, bạn có thể xem kết quả ở phần chính

### Bước 5: Xem báo cáo và xuất dữ liệu

- Xem các thẻ thông tin chi tiết
- Xuất báo cáo Excel hoặc báo cáo tùy chỉnh
- Ghi dữ liệu vào MariaDB nếu cần

---

## 🔧 Phần Sidebar

### Mapping Cột

- Cho phép bạn đổi tên cột nguồn về tên chuẩn
- Giúp ứng dụng đọc dữ liệu chính xác
- Nhấn `↩️ Reset về chuẩn` để trả về tên cột chuẩn

### Upload Dữ Liệu

- Tải file T1 và T2
- Hỗ trợ nhiều file để xử lý nhiều chi nhánh
- Ứng dụng tự động lưu file vào thư mục tạm

### Lịch Sử So Sánh

- Hiển thị lịch sử các lần chạy gần nhất
- Cho phép chọn lịch sử và tải lại dữ liệu cũ
- Hỗ trợ xuất lịch sử ra CSV
- Cho phép xóa cache cũ bằng nút `Dọn dẹp cache cũ`

---

## 📊 Các Tab Báo Cáo Chính

### Tab `📊 Tổng quan`

Hiển thị:

- KPI chính: số chi nhánh, tổng khách, tổng Δ
- Số lượng khách mở mới, tất toán, tăng
- Số cảnh báo rủi ro
- Biểu đồ xu hướng biến động theo loại

### Tab `📋 Chi tiết`

Bao gồm:

- `Chi Tiết Khách Hàng`
- `Thống Kê Theo Chi Nhánh`
- `Thống Kê Theo Phân Khúc`
- `Phân Khúc Nâng Cao`
- `Thống Kê Theo Nhóm Sản Phẩm`
- `Top Khách Hàng Tiêu Biểu`

### Tab `🔮 Dự báo`

Hiển thị:

- Dự báo T3 dựa trên động lượng T1 → T2
- Kịch bản cơ sở, lạc quan, thận trọng
- Độ tin cậy của dự báo
- Top chi nhánh có xu hướng giảm và tăng
- Biểu đồ xu hướng T1 → T2 → T3

### Tab `💡 Insights AI`

Hiển thị:

- Tóm tắt chiến lược nhanh
- Các gợi ý hành động quan trọng
- Những điểm dữ liệu cần chú ý

### Tab `⚠️ Cảnh báo`

Hiển thị:

- Cảnh báo chi nhánh giảm mạnh
- Nhóm biến động có DELTA âm lớn
- Khách hàng ưu tiên cấp cao cần xử lý
- Số outlier cần rà soát

### Tab `🎯 Khuyến nghị`

Hiển thị:

- Danh sách khách hàng cần hành động
- Mức ưu tiên: `RAT_CAO`, `CAO`, `TRUNG_BINH`
- Gợi ý hành động thực tế
- Bộ lọc theo chi nhánh, mức ưu tiên, nhóm hành động

### Tab `🛠️ Báo cáo tùy chỉnh`

Cho phép bạn:

- Chọn phần báo cáo muốn xuất
- Xuất file Excel chỉ chứa những phần đã chọn
- Tối ưu cho báo cáo trình lãnh đạo hoặc phòng KD

### Tab `💾 Báo cáo`

Cho phép:

- Xuất báo cáo Excel đầy đủ
- Xem mô tả nội dung từng sheet
- Tải file báo cáo tổng hợp

---

## 📌 Các Tính Năng Mới

### 1. Lịch sử và cache

- Lịch sử chạy được lưu lại
- Có thể tải lại kết quả cũ từ cache
- Xóa cache cũ để giải phóng ổ đĩa

### 2. Dự báo chi nhánh

- Dự báo theo momentum T1 → T2
- Dự báo cơ sở / lạc quan / thận trọng
- Giúp xác định chi nhánh cần giữ chân hoặc mở rộng

### 3. AI Insights

- Sinh ra insights dạng summary
- Xác định rủi ro và cơ hội nhanh
- Trực quan hóa bằng các thẻ thông tin

### 4. Ghi dữ liệu vào MariaDB

- Có thể ghi kết quả phân tích vào MariaDB
- Tự động tạo bảng nếu chưa tồn tại
- Hỗ trợ ghi đè dữ liệu khi cần

---

## 🧩 Chức Năng Chi Tiết và Ý Nghĩa

### Tải dữ liệu

- Mục đích: nhập dữ liệu nguồn T1 và T2 vào ứng dụng.
- Ý nghĩa: nếu phần này sai, mọi tính toán sau đó sẽ không chính xác.
- Kết quả: dữ liệu được lưu tạm và sẵn sàng để kiểm tra.

### Mapping Cột

- Mục đích: chuyển đổi tên cột trong file nguồn về định nghĩa chuẩn.
- Ý nghĩa: giúp ứng dụng đọc đúng trường như `MA_KH`, `CURRENT_BALANCE`, `DP_TYPE_CODE`.
- Kết quả: giảm lỗi khi file nguồn có tên cột hoặc cấu trúc khác nhau.

### Kiểm tra dữ liệu

- Mục đích: xác thực định dạng file, cột bắt buộc, và dữ liệu T1/T2.
- Ý nghĩa: phát hiện lỗi sớm trước khi so sánh, tiết kiệm thời gian và tránh sai sót.
- Kết quả: báo cáo lỗi rõ ràng nếu file không hợp lệ.

### So sánh dữ liệu

- Mục đích: tính các chỉ số chính giữa T1 và T2.
- Ý nghĩa: xác định khách hàng mới, khách tất toán, khách tăng/giảm, và khách không đổi.
- Kết quả: bảng kết quả chi tiết từng khách hàng, chi nhánh, phân khúc và sản phẩm.

### Lịch sử và Cache

- Mục đích: lưu kết quả chạy trước đó để có thể phục hồi nhanh.
- Ý nghĩa: tránh phải xử lý lại từ đầu khi bạn muốn xem lại kết quả đã chạy.
- Kết quả: danh sách lịch sử hiển thị các lần so sánh trước đó.

### Dự báo

- Mục đích: dự đoán xu hướng T3 dựa trên động lượng T1→T2.
- Ý nghĩa: giúp ra quyết định trước khi số liệu thực tế xuất hiện, tập trung vào chi nhánh có xu hướng tốt hoặc xấu.
- Kết quả: các kịch bản cơ sở, lạc quan, thận trọng và biểu đồ dự báo.

### Insights AI

- Mục đích: tổng hợp thông tin chính từ dữ liệu dưới dạng văn bản ngắn gọn.
- Ý nghĩa: giúp người dùng nhanh chóng nắm bắt điểm quan trọng mà không cần phân tích thủ công.
- Kết quả: nhận diện cơ hội, cảnh báo rủi ro và đề xuất điều chỉnh chiến lược.

### Khuyến nghị

- Mục đích: lựa chọn khách hàng và chi nhánh cần hành động.
- Ý nghĩa: biến dữ liệu thành hành động cụ thể cho bộ phận kinh doanh hoặc CSKH.
- Kết quả: danh sách ưu tiên với mức độ `RAT_CAO`, `CAO`, `TRUNG_BINH`.

### Xuất báo cáo

- Mục đích: tạo tệp Excel chuẩn để gửi cho quản lý hoặc lưu trữ.
- Ý nghĩa: giúp báo cáo chuyên nghiệp và dễ trình bày.
- Kết quả: một file Excel chứa các sheet rõ ràng như `Chi Tiết Khách Hàng`, `Theo Chi Nhánh`, `Bất Thường`, v.v.

### Ghi dữ liệu vào MariaDB

- Mục đích: lưu kết quả phân tích vào hệ quản trị để sử dụng chung.
- Ý nghĩa: dễ dàng tích hợp với báo cáo tập trung hoặc hệ thống BI.
- Kết quả: dữ liệu được ghi ra các bảng MariaDB, hỗ trợ truy vấn và báo cáo tự động.

### Dọn dẹp tệp tạm

- Mục đích: xóa các file tạm không cần thiết sau khi xử lý.
- Ý nghĩa: giữ ổ cứng sạch và tránh lỗi đầy bộ nhớ tạm.
- Kết quả: ứng dụng vận hành ổn định hơn trên Windows.

---

## 💾 Cách Ghi Dữ Liệu Lên MariaDB

### Trường thông tin cần nhập:

- **Host**: địa chỉ máy chủ MariaDB
- **Port**: 3306 (mặc định)
- **User**: tài khoản MariaDB
- **Password**: mật khẩu
- **Database**: tên database
- **Tiền tố bảng**: ví dụ `deposit_`
- **Ghi đè bảng nếu tồn tại**: chọn nếu muốn reset dữ liệu

### Bước thực hiện:

1. Vào tab `💾 Xuất Báo Cáo`
2. Mở expander `📡 Lưu dữ liệu vào MariaDB`
3. Điền thông tin kết nối
4. Nhấn `📤 Ghi dữ liệu lên MariaDB`

### Bảng sẽ được lưu:

- `deposit_comparison`
- `deposit_summary_branch`
- `deposit_summary_cust_type`
- `deposit_summary_product`
- `deposit_segment_summary`
- `deposit_alert_summary`
- `deposit_recommendations`
- `deposit_driver_analysis`
- `deposit_prediction`

---

## 🧠 Giải Thích Các Loại Biến Động

- `MO_MOI`: khách hàng mới
- `TAT_TOAN`: khách hàng đã tất toán
- `TANG`: khách hàng có dư tiền tăng
- `GIAM`: khách hàng giảm dư tiền
- `KHONG_DOI`: không thay đổi

---

## 💡 Mẹo Sử Dụng

### Tiến hành phân tích nhanh

1. Upload dữ liệu và validate
2. So sánh để tạo kết quả
3. Xem tab `🔮 Dự báo` để xác định chi nhánh rủi ro
4. Xem tab `💡 Insights AI` để ra quyết định nhanh
5. Xem tab `🎯 Khuyến nghị` để chọn khách cần xử lý
6. Xuất báo cáo hoặc ghi vào MariaDB

### Khi có lỗi không gian lưu trữ

- Ứng dụng sẽ sử dụng thư mục tạm
- Nếu hết ổ, bạn nên dọn thư mục TEMP
- Ứng dụng có cơ chế tự dọn tệp tạm sau khi xử lý

---

## 📄 Ghi chú quan trọng

- Nếu dữ liệu nguồn khác tên, hãy sử dụng mục `Mapping Cột`
- Mỗi lần thay đổi mapping phải validate lại
- Kết quả lịch sử chỉ có thể tải lại khi cache hợp lệ
- MariaDB cần database tồn tại trước khi ghi

---

## 📍 Troubleshooting

### Lỗi `No space left on device`

- Giải phóng dung lượng ổ chứa TEMP
- Xóa file tạm cũ trên Windows: `C:\Users\<User>\AppData\Local\Temp`
- Khởi động lại app sau khi dọn dẹp

### Lỗi `KeyError: cache_key`

- Do lịch sử cũ không có trường cache_key
- Chạy lại từ đầu để tạo lịch sử mới

### Lỗi kết nối MariaDB

- Kiểm tra host/port/user/password
- Đảm bảo database đã được tạo sẵn

---

## 📌 Tổng kết

Ứng dụng hiện đã hỗ trợ:

- So sánh dữ liệu T1/T2
- Lọc và phân tích khách hàng chi tiết
- Phát hiện outlier
- Xuất báo cáo Excel đầy đủ
- Dự báo và insights
- Ghi dữ liệu vào MariaDB
- Quản lý lịch sử và cache

Chúc bạn sử dụng hiệu quả và nhanh chóng tìm được những nhóm khách hàng cần ưu tiên cạnh tranh!

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
