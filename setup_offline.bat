@echo off
REM ========================================
REM Hệ Thống So Sánh Dữ Liệu Tiền Gửi
REM Setup Script Offline (Windows)
REM ========================================

echo.
echo ╔════════════════════════════════════════════════════╗
echo ║   CÀI ĐẶT OFFLINE - HỆ THỐNG SO SÁNH TIỀN GỬI      ║
echo ╚════════════════════════════════════════════════════╝
echo.

REM Kiểm tra Python 
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Lỗi: Python không được cài đặt!
    echo.
    echo Vui lòng cài đặt Python từ https://www.python.org
    echo Hoặc copy Python từ máy khác.
    echo.
    pause
    exit /b 1
)

echo ✅ Phát hiện Python
python --version
echo.

REM Kiểm tra thư mục wheels
if not exist wheels (
    echo ❌ Lỗi: Thư mục 'wheels' không tồn tại!
    echo.
    echo Hãy:
    echo 1. Quay lại máy có Internet
    echo 2. Chạy: pip download -r requirements.txt -d wheels
    echo 3. Chuyển toàn bộ project sang máy này
    echo.
    pause
    exit /b 1
)

echo ✅ Thư mục 'wheels' tồn tại
echo.

REM Tạo virtual environment
echo 📦 Đang tạo virtual environment...
python -m venv venv
if errorlevel 1 (
    echo ❌ Lỗi: Không thể tạo venv
    pause
    exit /b 1
)
echo ✅ Virtual environment đã tạo
echo.

REM Kích hoạt venv
echo 🔄 Đang kích hoạt virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ❌ Lỗi: Không thể kích hoạt venv
    pause
    exit /b 1
)
echo ✅ Virtual environment đã kích hoạt
echo.

REM Cập nhật pip
echo 🔧 Đang cập nhật pip...
python -m pip install --upgrade pip --no-index --find-links=wheels >nul 2>&1
echo ✅ Pip đã cập nhật
echo.

REM Cài đặt packages
echo 📥 Đang cài đặt packages từ thư mục wheels...
echo    (Quá trình này có thể mất vài phút)
pip install --no-index --find-links=wheels -r requirements.txt
if errorlevel 1 (
    echo ❌ Lỗi: Không thể cài đặt packages
    echo.
    echo Kiểm tra:
    echo - Thư mục wheels có đầy đủ không?
    echo - File requirements.txt có đúng không?
    echo.
    pause
    exit /b 1
)
echo ✅ Tất cả packages đã cài đặt
echo.

REM Kiểm tra cài đặt
echo 🔍 Đang kiểm tra cài đặt...
pip show streamlit >nul 2>&1
if errorlevel 1 (
    echo ❌ Lỗi: Streamlit chưa được cài đặt
    pause
    exit /b 1
)
echo ✅ Streamlit đã cài đặt thành công
echo.

REM In hướng dẫn tiếp theo
echo.
echo ╔════════════════════════════════════════════════════╗
echo ║          ✅ CÀI ĐẶT HOÀN TẤT!                     ║
echo ╚════════════════════════════════════════════════════╝
echo.
echo 🚀 Để chạy ứng dụng:
echo.
echo    1. Mở Command Prompt (cmd) hoặc PowerShell
echo.
echo    2. Vào thư mục project:
echo       cd %cd%
echo.
echo    3. Kích hoạt virtual environment:
echo       venv\Scripts\activate
echo.
echo    4. Chạy ứng dụng:
echo       streamlit run app.py
echo.
echo    5. Mở trình duyệt:
echo       http://localhost:8501
echo.
echo ℹ️  Lưu Ý:
echo    - Bạn có thể tắt terminal này
echo    - Mỗi lần chạy cần kích hoạt venv trước
echo    - Để dừng ứng dụng: Ctrl+C
echo.
pause
