"""
Configuration file for the deposit comparison system.
Modify these settings to customize the application behavior.
"""

# ==================== FILE VALIDATION ====================

# File name pattern: {MA_CN}_dp01_yyyymmdd.csv
FILE_PATTERN = r'^(\d{4})_dp01_(\d{8})\.csv$'

# Required columns in CSV
REQUIRED_COLUMNS = ['MA_KH', 'TEN_KH', 'DP_TYPE', 'CURRENT_BALANCE', 'CUST_TYPE_NAME']

# ==================== DATA FILTERING ====================

# DP_TYPE_CODEs to exclude from analysis
EXCLUDE_DP_TYPES = ["401", "101"]

# ==================== PRODUCT GROUP MAPPING ====================

DP_TYPE_MAPPING = {
    # Tiết kiệm
    '010': 'TIET_KIEM',
    '011': 'TIET_KIEM',
    '012': 'TIET_KIEM',
    # Có kỳ hạn
    '020': 'CO_KY_HAN',
    '021': 'CO_KY_HAN',
    '022': 'CO_KY_HAN',
    '050': 'CO_KY_HAN',
    # Không kỳ hạn
    '030': 'KHONG_KY_HAN',
    '031': 'KHONG_KY_HAN',
    '032': 'KHONG_KY_HAN',
    '040': 'KHONG_KY_HAN',
    '100': 'KHONG_KY_HAN',
    '102': 'KHONG_KY_HAN',
    '103': 'KHONG_KY_HAN',
    '104': 'KHONG_KY_HAN',
    '105': 'KHONG_KY_HAN',
    '106': 'KHONG_KY_HAN',
    '107': 'KHONG_KY_HAN',
    '108': 'KHONG_KY_HAN',
    '109': 'KHONG_KY_HAN',
    '110': 'KHONG_KY_HAN',
    '111': 'KHONG_KY_HAN',
    '112': 'KHONG_KY_HAN',
    '113': 'KHONG_KY_HAN',
    '114': 'KHONG_KY_HAN',
    '115': 'KHONG_KY_HAN',
    '116': 'KHONG_KY_HAN',
    '117': 'KHONG_KY_HAN',
    '118': 'KHONG_KY_HAN',
    '119': 'KHONG_KY_HAN',
}

# ==================== OUTLIER DETECTION ====================

# Method: 'iqr' or 'zscore'
OUTLIER_METHOD = 'iqr'

# IQR multiplier (default 1.5 = standard outlier definition)
# Higher value = more conservative (fewer outliers detected)
IQR_MULTIPLIER = 1.5

# Z-score threshold (default 3.0 = 99.7% confidence)
# Lower value = more sensitive (more outliers detected)
ZSCORE_THRESHOLD = 3.0

# ==================== EXPORT SETTINGS ====================

# Number of rows to show for top outliers in tab
TOP_OUTLIERS_COUNT = 50

# ==================== DISPLAY SETTINGS ====================

# Number of decimal places for currency
CURRENCY_DECIMALS = 0

# Number of decimal places for percentage
PERCENTAGE_DECIMALS = 2

# ==================== CHANGE TYPES ====================

CHANGE_TYPES = {
    'MO_MOI': 'Mở Mới',
    'TAT_TOAN': 'Tất Toán',
    'TANG': 'Tăng',
    'GIAM': 'Giảm',
    'KHONG_DOI': 'Không Đổi'
}

# ==================== PRODUCT GROUPS ====================

PRODUCT_GROUPS = {
    'TIET_KIEM': 'Tiết Kiệm',
    'CO_KY_HAN': 'Có Kỳ Hạn',
    'KHONG_KY_HAN': 'Không Kỳ Hạn'
}

# ==================== STREAMLIT UI SETTINGS ====================

# Page title
PAGE_TITLE = "Hệ Thống So Sánh Dữ Liệu Tiền Gửi"

# Page icon
PAGE_ICON = "📊"

# Layout
PAGE_LAYOUT = "wide"

# Color scheme for charts
CHART_COLOR_SCALE = ['red', 'yellow', 'green']
