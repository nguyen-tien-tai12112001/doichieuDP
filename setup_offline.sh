#!/bin/bash

###########################################################
# Hệ Thống So Sánh Dữ Liệu Tiền Gửi
# Setup Script Offline (Linux/Mac)
###########################################################

echo ""
echo "╔════════════════════════════════════════════════════╗"
echo "║   CÀI ĐẶT OFFLINE - HỆ THỐNG SO SÁNH TIỀN GỬI     ║"
echo "╚════════════════════════════════════════════════════╝"
echo ""

# Kiểm tra Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Lỗi: Python không được cài đặt!"
    echo ""
    echo "Vui lòng cài đặt Python:"
    echo "  macOS: brew install python3"
    echo "  Linux: sudo apt-get install python3.11"
    echo ""
    read -p "Nhấn Enter để thoát..."
    exit 1
fi

echo "✅ Phát hiện Python"
python3 --version
echo ""

# Kiểm tra thư mục wheels
if [ ! -d "wheels" ]; then
    echo "❌ Lỗi: Thư mục 'wheels' không tồn tại!"
    echo ""
    echo "Hãy:"
    echo "1. Quay lại máy có Internet"
    echo "2. Chạy: pip download -r requirements.txt -d wheels"
    echo "3. Chuyển toàn bộ project sang máy này"
    echo ""
    read -p "Nhấn Enter để thoát..."
    exit 1
fi

echo "✅ Thư mục 'wheels' tồn tại"
echo ""

# Tạo virtual environment
echo "📦 Đang tạo virtual environment..."
python3 -m venv venv
if [ $? -ne 0 ]; then
    echo "❌ Lỗi: Không thể tạo venv"
    read -p "Nhấn Enter để thoát..."
    exit 1
fi
echo "✅ Virtual environment đã tạo"
echo ""

# Kích hoạt venv
echo "🔄 Đang kích hoạt virtual environment..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "❌ Lỗi: Không thể kích hoạt venv"
    read -p "Nhấn Enter để thoát..."
    exit 1
fi
echo "✅ Virtual environment đã kích hoạt"
echo ""

# Cập nhật pip
echo "🔧 Đang cập nhật pip..."
python -m pip install --upgrade pip --no-index --find-links=wheels > /dev/null 2>&1
echo "✅ Pip đã cập nhật"
echo ""

# Cài đặt packages
echo "📥 Đang cài đặt packages từ thư mục wheels..."
echo "    (Quá trình này có thể mất vài phút)"
pip install --no-index --find-links=wheels -r requirements.txt
if [ $? -ne 0 ]; then
    echo "❌ Lỗi: Không thể cài đặt packages"
    echo ""
    echo "Kiểm tra:"
    echo "- Thư mục wheels có đầy đủ không?"
    echo "- File requirements.txt có đúng không?"
    echo ""
    read -p "Nhấn Enter để thoát..."
    exit 1
fi
echo "✅ Tất cả packages đã cài đặt"
echo ""

# Kiểm tra cài đặt
echo "🔍 Đang kiểm tra cài đặt..."
pip show streamlit > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "❌ Lỗi: Streamlit chưa được cài đặt"
    read -p "Nhấn Enter để thoát..."
    exit 1
fi
echo "✅ Streamlit đã cài đặt thành công"
echo ""

# In hướng dẫn tiếp theo
echo ""
echo "╔════════════════════════════════════════════════════╗"
echo "║          ✅ CÀI ĐẶT HOÀN TẤT!                     ║"
echo "╚════════════════════════════════════════════════════╝"
echo ""
echo "🚀 Để chạy ứng dụng:"
echo ""
echo "    1. Mở Terminal"
echo ""
echo "    2. Vào thư mục project:"
echo "       cd $(pwd)"
echo ""
echo "    3. Kích hoạt virtual environment:"
echo "       source venv/bin/activate"
echo ""
echo "    4. Chạy ứng dụng:"
echo "       streamlit run app.py"
echo ""
echo "    5. Mở trình duyệt:"
echo "       http://localhost:8501"
echo ""
echo "ℹ️  Lưu Ý:"
echo "    - Bạn có thể tắt terminal này"
echo "    - Mỗi lần chạy cần kích hoạt venv trước"
echo "    - Để dừng ứng dụng: Ctrl+C"
echo ""
