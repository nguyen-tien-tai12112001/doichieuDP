# Thuyết Trình Ứng Dụng So Sánh Dữ Liệu Tiền Gửi

## 1. Giới thiệu chung

### 1.1 Mục tiêu

- Giới thiệu ứng dụng phân tích và so sánh dữ liệu tiền gửi ngân hàng giữa 2 kỳ.
- Trình bày cách ứng dụng giúp phát hiện khách hàng mới, khách tất toán, khách tăng/giảm và bất thường.
- Minh họa khả năng xuất báo cáo Excel và ghi dữ liệu kết quả lên MariaDB.

### 1.2 Vấn đề cần giải quyết

- Dữ liệu tiền gửi trên nhiều chi nhánh và kỳ có thể khó so sánh thủ công.
- Mất nhiều thời gian để tìm khách hàng đáng chú ý, ra quyết định nhanh và chuẩn.
- Thiếu hệ thống báo cáo tự động và lưu trữ kết quả để đối chiếu sau này.

## 2. Giải pháp ứng dụng

### 2.1 Tổng quan chức năng

- Upload dữ liệu T1 và T2.
- Kiểm tra, mapping cột và validate dữ liệu.
- So sánh chi tiết theo khách hàng, chi nhánh, phân khúc và sản phẩm.
- Phát hiện outlier bằng phương pháp IQR.
- Tạo dự báo cơ bản cho kỳ tiếp theo.
- Sinh insights AI nhanh và khuyến nghị hành động.
- Xuất báo cáo Excel và ghi dữ liệu vào MariaDB.
- Lưu lịch sử chạy và cache để phục hồi nhanh.

### 2.2 Giá trị chính

- Tiết kiệm thời gian phân tích dữ liệu so sánh.
- Giảm sai sót do xử lý thủ công.
- Hỗ trợ ra quyết định nhanh thông qua insights và recommendation.
- Giúp bộ phận kinh doanh/CSKH tập trung khách hàng quan trọng.
- Dễ dùng cho thuyết trình, trình bày kết quả và chia sẻ báo cáo.

## 3. Các tính năng chi tiết

### 3.1 Upload và Mapping Cột

- Cho phép upload nhiều file CSV của T1 và T2.
- Hỗ trợ đổi tên cột nguồn để khớp với định dạng chuẩn.
- Giúp xử lý dữ liệu nguồn không đồng nhất.

### 3.2 Validate dữ liệu

- Kiểm tra định dạng file, cột bắt buộc và sự đồng bộ giữa T1/T2.
- Phát hiện lỗi sớm trước khi tiến hành so sánh.
- Tránh kết quả sai do dữ liệu thiếu hoặc sai cột.

### 3.3 So sánh chính

- Phân tích biến động theo khách hàng:
  - Khách mới (MO_MOI)
  - Khách tất toán (TAT_TOAN)
  - Khách tăng (TANG)
  - Khách giảm (GIAM)
  - Khách không đổi (KHONG_DOI)
- Tổng hợp theo chi nhánh, phân khúc và sản phẩm.
- Tính DELTA và tỷ lệ tăng trưởng.

### 3.4 Bất thường và outlier

- Sử dụng phương pháp IQR để xác định outlier.
- Tự động cảnh báo các biến động lớn bất thường.
- Hỗ trợ rà soát khách hàng hoặc dòng tiền cần kiểm tra.

### 3.5 Dự báo

- Dự đoán xu hướng T3 dựa trên chuyển động T1→T2.
- Hiển thị kịch bản cơ sở, lạc quan và thận trọng.
- Dùng để định hướng chiến lược chi nhánh và ưu tiên chăm sóc.

### 3.6 Insights AI

- Tóm tắt nhanh các điểm nổi bật trên dữ liệu.
- Đề xuất hành động cần ưu tiên.
- Tăng tính trực quan khi trình bày với lãnh đạo.

### 3.7 Khuyến nghị hành động

- Xây dựng danh sách khách hàng hoặc chi nhánh cần ưu tiên.
- Gắn mức độ ưu tiên: `RAT_CAO`, `CAO`, `TRUNG_BINH`.
- Hướng dẫn bộ phận kinh doanh xử lý tiếp theo.

### 3.8 Xuất báo cáo và MariaDB

- Xuất file Excel chuẩn với nhiều sheet.
- Ghi dữ liệu phân tích lên MariaDB để dùng chung.
- Hỗ trợ bảng dữ liệu quay lại cho BI hoặc báo cáo tự động.

### 3.9 Lịch sử và cache

- Lưu kết quả chạy trước đó.
- Cho phép chọn lịch sử và tải lại dữ liệu cũ.
- Giảm thời gian xử lý khi cần so sánh lại.

## 4. Hướng dẫn demo thuyết trình

### 4.1 Kịch bản trình bày

1. Giới thiệu bài toán và nhu cầu của ngân hàng.
2. Trình bày giao diện ứng dụng và các bước thao tác.
3. Upload file T1/T2 và check dữ liệu.
4. Chạy phần so sánh và xem kết quả chính.
5. Chuyển sang tab bất thường và phân tích outlier.
6. Hiển thị phần dự báo và insights AI.
7. Trình bày cách xuất báo cáo và ghi dữ liệu lên MariaDB.
8. Kết luận về giá trị mang lại và bước tiếp theo.

### 4.2 Slide đề xuất

- Slide 1: Tiêu đề và mục tiêu.
- Slide 2: Thách thức hiện tại.
- Slide 3: Giải pháp tổng quan.
- Slide 4: Quy trình sử dụng ứng dụng.
- Slide 5: Kết quả phân tích chính (biến động, outlier).
- Slide 6: Dự báo và insights.
- Slide 7: Xuất báo cáo và lưu trữ dữ liệu.
- Slide 8: Tổng kết và đề xuất hành động.

### 4.3 Điểm nhấn khi thuyết trình

- Nêu rõ lợi ích so sánh nhanh giữa 2 kỳ.
- Chỉ ra tính năng phát hiện khách hàng quan trọng.
- Nhấn mạnh khả năng tạo báo cáo tự động.
- Giới thiệu phần ghi dữ liệu vào MariaDB để mở rộng hệ thống.

## 5. Thông tin kỹ thuật

### 5.1 Công nghệ chính

- Python
- Streamlit
- Pandas, Plotly
- SQLite (cache nội bộ)
- MariaDB (tùy chọn lưu kết quả)

### 5.2 Luồng xử lý

- Upload file → validate → xử lý so sánh → tạo báo cáo → xuất/ghi dữ liệu.
- Lưu cache để phục hồi kết quả trước.
- Dọn tệp tạm tự động để tránh đầy ổ đĩa.

### 5.3 Dữ liệu đầu vào

- File CSV với định dạng tên `MA_CN_dp01_yyyymmdd.csv`.
- Cột tối thiểu: `MA_KH`, `TEN_KH`, `DP_TYPE_CODE`, `CURRENT_BALANCE`, `CUST_TYPE_NAME`.
- Có thể mapping cột nếu tên cột khác.

## 6. Gợi ý tương tác với NotebookLM

- Copy toàn bộ nội dung file này vào NotebookLM.
- Yêu cầu NotebookLM tạo slide, tóm tắt hoặc ghi chú trình bày.
- Ví dụ prompt: `Dựa trên nội dung này, hãy tạo outline bài thuyết trình gồm 8 slide và ghi chú người nói.`

## 7. Kết luận

Ứng dụng là một công cụ báo cáo và phân tích thực tế cho ngân hàng:

- Hỗ trợ so sánh dữ liệu nhanh.
- Giúp tìm khách hàng và chi nhánh cần quan tâm.
- Gợi ý hành động dựa trên dữ liệu.
- Đơn giản hóa việc chuẩn bị báo cáo cho lãnh đạo.

Chúc bạn có buổi thuyết trình thành công!
