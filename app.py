"""
Main Streamlit application for deposit comparison system.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import hashlib
from pathlib import Path
import os
import io
import json
import re
from datetime import datetime
import tempfile
import shutil
from typing import Dict, List, Tuple, Optional
import pickle
import sqlite3
try:
    import pymysql
except ImportError:
    pymysql = None
from contextlib import contextmanager

# Import custom modules
from validators import validate_all_files, ValidationError
from loader import load_and_normalize_csv, filter_valid_data, load_branch_data
from aggregator import group_by_customer, aggregate_pair
from compare_engine import merge_and_compare, process_all_branches
from summary_engine import (
    summary_by_branch, summary_by_customer_type, summary_by_product_group,
    summary_by_change_type, get_dp_type_mapping
)
from outlier_engine import detect_outliers_iqr, get_outliers_summary, analyze_outliers
from exporter import export_to_excel
from interest_rate_fetcher import get_interest_rate_insights
from ai_insights import (
    perform_customer_segmentation,
    predict_churn_risk,
    generate_ai_recommendations
)
from sharing import render_sharing_interface, render_shared_analysis_viewer
from data_warehouse import (
    init_warehouse_tables, import_file_to_warehouse, import_files_batch,
    list_warehouse_files, delete_warehouse_file, delete_warehouse_files_batch,
    get_warehouse_stats, get_file_path, get_file_info, get_warehouse_files_by_branch,
    suggest_file_pairs
)
from warehouse_ui import (
    build_comparison_from_warehouse,
    render_calendar_view,
    render_enhanced_file_list,
    render_import_section,
    render_statistics_section,
)
from auth_manager import log_audit


DATABASE_FILE = Path('app_database.db')

SEGMENT_BUCKETS = [
    ('<50M', 0, 50_000_000),
    ('50-200M', 50_000_000, 200_000_000),
    ('200-500M', 200_000_000, 500_000_000),
    ('>500M', 500_000_000, float('inf')),
]
ALERT_BRANCH_DROP_RATE = -0.05
ALERT_BRANCH_DELTA_THRESHOLD = 100_000_000
ALERT_PRODUCT_DELTA_THRESHOLD = 150_000_000
ALERT_OUTLIER_THRESHOLD = 5


@contextmanager
def get_db_connection():
    """Context manager for database connections."""
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    try:
        yield conn
    finally:
        conn.close()


def filter_files_by_branch_access(df: pd.DataFrame) -> pd.DataFrame:
    """Return all warehouse files without branch access filtering."""
    return df


def init_database():
    """Initialize database tables if they don't exist."""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # History table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS comparison_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                cache_key TEXT UNIQUE,
                t1_input_files TEXT,
                t2_input_files TEXT,
                t1_files INTEGER,
                t2_files INTEGER,
                t1_date TEXT,
                t2_date TEXT,
                branches INTEGER,
                customers INTEGER,
                total_t1 REAL,
                total_t2 REAL,
                total_delta REAL,
                high_risk_customers INTEGER,
                cache_hit TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Processed data cache table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS processed_data_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cache_key TEXT UNIQUE NOT NULL,
                data_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # User settings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                setting_key TEXT UNIQUE NOT NULL,
                setting_value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()

    # Initialize warehouse tables
    init_warehouse_tables()


def save_history_to_db(entry: Dict[str, str]) -> None:
    """Save comparison history to database."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO comparison_history
            (timestamp, cache_key, t1_input_files, t2_input_files, t1_files, t2_files,
             t1_date, t2_date, branches, customers, total_t1, total_t2, total_delta,
             high_risk_customers, cache_hit)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            entry.get('timestamp'),
            entry.get('cache_key'),
            entry.get('t1_input_files'),
            entry.get('t2_input_files'),
            entry.get('t1_files'),
            entry.get('t2_files'),
            entry.get('t1_date'),
            entry.get('t2_date'),
            entry.get('branches'),
            entry.get('customers'),
            entry.get('total_t1'),
            entry.get('total_t2'),
            entry.get('total_delta'),
            entry.get('high_risk_customers'),
            entry.get('cache_hit')
        ))
        conn.commit()


def load_history_from_db(limit: int = 20) -> pd.DataFrame:
    """Load recent processing history from database."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT timestamp, cache_key, t1_input_files, t2_input_files, t1_files, t2_files,
                   t1_date, t2_date, branches, customers, total_t1, total_t2, total_delta,
                   high_risk_customers, cache_hit
            FROM comparison_history
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))
        rows = cursor.fetchall()

        if not rows:
            return pd.DataFrame()

        # Convert to DataFrame
        data = []
        for row in rows:
            data.append({
                'timestamp': row['timestamp'],
                'cache_key': row['cache_key'],
                't1_input_files': row['t1_input_files'],
                't2_input_files': row['t2_input_files'],
                't1_files': row['t1_files'],
                't2_files': row['t2_files'],
                't1_date': row['t1_date'],
                't2_date': row['t2_date'],
                'branches': row['branches'],
                'customers': row['customers'],
                'total_t1': row['total_t1'],
                'total_t2': row['total_t2'],
                'total_delta': row['total_delta'],
                'high_risk_customers': row['high_risk_customers'],
                'cache_hit': row['cache_hit']
            })

        return pd.DataFrame(data)


def save_processed_data_to_db(cache_key: str, processed_data: Dict) -> None:
    """Save processed data to database cache."""
    try:
        # Serialize the data using pickle (better for pandas DataFrames)
        import pickle
        data_blob = pickle.dumps(processed_data)

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO processed_data_cache
                (cache_key, data_json, last_accessed)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            ''', (cache_key, data_blob))
            conn.commit()
    except Exception as e:
        st.warning(f"Không thể lưu cache vào database: {e}")


def load_processed_data_from_db(cache_key: str) -> Dict:
    """Load processed data from database cache."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT data_json FROM processed_data_cache
                WHERE cache_key = ?
            ''', (cache_key,))
            row = cursor.fetchone()

            if row:
                # Update last accessed time
                cursor.execute('''
                    UPDATE processed_data_cache
                    SET last_accessed = CURRENT_TIMESTAMP
                    WHERE cache_key = ?
                ''', (cache_key,))
                conn.commit()

                # Deserialize the data - handle both old JSON and new pickle formats
                data = row['data_json']
                import pickle

                # Try pickle first (new format)
                try:
                    loaded_data = pickle.loads(data)
                    # Ensure it's a dict
                    return loaded_data if isinstance(loaded_data, dict) else {}
                except (TypeError, pickle.UnpicklingError):
                    # Fall back to JSON (old format) - but this will return strings, not DataFrames
                    # So we'll return empty dict to force re-processing
                    placeholder = st.container(key='info_cache_format')
                    placeholder.info("Cache cũ không tương thích, sẽ tạo cache mới.")
                    return {}
    except Exception as e:
        st.warning(f"Không thể tải cache từ database: {e}")

    return {}


def cleanup_old_cache(days: int = 30) -> None:
    """Clean up old cache entries older than specified days."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM processed_data_cache
                WHERE last_accessed < datetime('now', '-{} days')
            '''.format(days))
            deleted_count = cursor.rowcount
            conn.commit()

            if deleted_count > 0:
                placeholder = st.container(key='info_cache_cleanup')
                placeholder.info(f"Đã dọn dẹp {deleted_count} cache entries cũ")
    except Exception as e:
        st.warning(f"Lỗi khi dọn dẹp cache: {e}")


# Initialize database on startup
init_database()

SEGMENT_BUCKETS = [
    ('<50M', 0, 50_000_000),
    ('50-200M', 50_000_000, 200_000_000),
    ('200-500M', 200_000_000, 500_000_000),
    ('>500M', 500_000_000, float('inf')),
]
ALERT_BRANCH_DROP_RATE = -0.05
ALERT_BRANCH_DELTA_THRESHOLD = 100_000_000
ALERT_PRODUCT_DELTA_THRESHOLD = 150_000_000
ALERT_OUTLIER_THRESHOLD = 5


# Configure page
st.set_page_config(
    page_title="Hệ Thống So Sánh Dữ Liệu Tiền Gửi",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add enhanced CSS styling
st.markdown("""
<style>
    .main-header {
        color: #1f77b4;
        font-size: 2.8rem;
        font-weight: bold;
        margin-bottom: 10px;
        text-align: center;
    }
    .sub-header {
        color: #666;
        font-size: 1.1rem;
        margin-bottom: 30px;
        text-align: center;
    }
    .step-guide {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .step-guide h3 {
        margin-top: 0;
    }
    .info-box {
        background-color: #e7f3ff;
        border-left: 4px solid #2196F3;
        padding: 15px;
        border-radius: 5px;
        margin: 15px 0;
    }
    .success-box {
        background-color: #e8f5e9;
        border-left: 4px solid #4CAF50;
        padding: 15px;
        border-radius: 5px;
        margin: 15px 0;
    }
    .warning-box {
        background-color: #fff3e0;
        border-left: 4px solid #FF9800;
        padding: 15px;
        border-radius: 5px;
        margin: 15px 0;
    }
    .metric-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    .stTabs [data-baseweb="tab-list"] button {
        font-size: 16px;
        font-weight: 600;
    }
    [data-testid="stSidebar"] {
        background: #f8fafc;
        border-right: 1px solid #e5e7eb;
    }
    [data-testid="stSidebar"] .stButton>button {
        justify-content: flex-start;
        border-radius: 8px;
        min-height: 42px;
        font-weight: 600;
        border: 1px solid #e5e7eb;
    }
    [data-testid="stSidebar"] .stButton>button[kind="primary"] {
        background: #0f766e;
        border-color: #0f766e;
        color: white;
    }
    .sidebar-brand {
        padding: 10px 4px 18px 4px;
        margin-bottom: 8px;
        border-bottom: 1px solid #e5e7eb;
    }
    .sidebar-brand-title {
        color: #0f172a;
        font-size: 1.35rem;
        font-weight: 800;
        line-height: 1.1;
    }
    .sidebar-brand-subtitle {
        color: #64748b;
        font-size: 0.85rem;
        margin-top: 4px;
    }
    @media (max-width: 900px) {
        .main-header {
            font-size: 2rem;
        }
        .sub-header {
            font-size: 0.95rem;
        }
        .metric-card, .step-guide, .info-box, .success-box, .warning-box {
            padding: 14px;
        }
        .stButton>button, .stDownloadButton>button {
            width: 100% !important;
            min-width: unset !important;
        }
        .css-1d391kg, .css-1ydfahe {
            padding: 8px !important;
        }
    }
</style>
""", unsafe_allow_html=True)

def init_session_state() -> None:
    """Initialize session state keys used by the app."""
    defaults = {
        'processed_data': None,
        'history_loaded_data': None,
        'processing_cache': {},
        'selected_t1_files': [],
        'selected_t2_files': [],
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def get_active_analysis_data() -> Optional[Dict]:
    """Return the currently active analysis payload for the app."""
    if st.session_state.get('history_loaded_data') is not None:
        data = st.session_state['history_loaded_data']
        # Ensure it's a dict, not a DataFrame
        return data if isinstance(data, dict) else None
    data = st.session_state.get('processed_data')
    # Ensure it's a dict, not a DataFrame
    return data if isinstance(data, dict) else None


def save_uploaded_files(files, temp_dir: str) -> List[str]:
    """Persist uploaded files to temporary directory."""
    paths = []
    for file in files:
        path = os.path.join(temp_dir, file.name)
        with open(path, 'wb') as f:
            f.write(file.getbuffer())
        paths.append(path)
    return paths


def cleanup_temp_dir(temp_dir: str) -> None:
    """Remove temporary directory if it still exists."""
    if not temp_dir:
        return
    try:
        if os.path.isdir(temp_dir):
            shutil.rmtree(temp_dir)
    except Exception as e:
        st.warning(f"Không thể xóa thư mục tạm: {e}")


def collect_file_metadata(files) -> List[Dict[str, str]]:
    """Collect filename and content hash for cache/history."""
    metadata = []
    for file in files:
        raw = file.getvalue()
        digest = hashlib.sha256(raw).hexdigest()
        metadata.append({'name': file.name, 'sha256': digest})
    return sorted(metadata, key=lambda x: x['name'])


def append_history(entry: Dict[str, str]) -> None:
    """Append one processing record to database."""
    save_history_to_db(entry)


def save_processed_data(cache_key: str, processed_data: Dict) -> None:
    """Save processed data to database cache."""
    save_processed_data_to_db(cache_key, processed_data)


def load_processed_data(cache_key: str) -> Dict:
    """Load processed data from database cache."""
    return load_processed_data_from_db(cache_key)


def load_history(limit: int = 20) -> pd.DataFrame:
    """Load recent processing history from database."""
    return load_history_from_db(limit)


def sanitize_sql_name(name: str) -> str:
    safe_name = re.sub(r'\s+', '_', str(name).strip())
    safe_name = re.sub(r'[^0-9a-zA-Z_]', '_', safe_name)
    if not safe_name:
        safe_name = 'column'
    if safe_name[0].isdigit():
        safe_name = 'c_' + safe_name
    return safe_name[:64]


def parse_filename_date(filename: str) -> Optional[str]:
    """Extract date string from filename if it follows the expected pattern."""
    match = re.match(r'^(\d{4})_dp01_(\d{8})\.csv$', filename)
    return match.group(2) if match else None


def build_mariadb_table_schema(df: pd.DataFrame) -> str:
    cols = []
    for col in df.columns:
        colname = sanitize_sql_name(col)
        dtype = df[col].dtype
        if pd.api.types.is_integer_dtype(dtype):
            sql_type = 'BIGINT'
        elif pd.api.types.is_float_dtype(dtype):
            sql_type = 'DOUBLE'
        elif pd.api.types.is_bool_dtype(dtype):
            sql_type = 'TINYINT'
        elif pd.api.types.is_datetime64_any_dtype(dtype):
            sql_type = 'DATETIME'
        else:
            sql_type = 'TEXT'
        cols.append(f'`{colname}` {sql_type}')
    return ', '.join(cols)


def get_mariadb_connection(host: str, port: int, user: str, password: str, database: str):
    if pymysql is None:
        raise ImportError("Chưa cài pymysql. Cài thêm gói pymysql để dùng tính năng ghi MariaDB.")
    return pymysql.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
    )


def create_mariadb_table(cursor, table_name: str, df: pd.DataFrame) -> None:
    safe_table = sanitize_sql_name(table_name)
    schema = build_mariadb_table_schema(df)
    create_sql = f"CREATE TABLE IF NOT EXISTS `{safe_table}` (id BIGINT AUTO_INCREMENT PRIMARY KEY, {schema})"
    cursor.execute(create_sql)


def write_dataframe_to_mariadb(cursor, table_name: str, df: pd.DataFrame, overwrite: bool = False) -> int:
    safe_table = sanitize_sql_name(table_name)
    if overwrite:
        cursor.execute(f"TRUNCATE TABLE `{safe_table}`")

    columns = [sanitize_sql_name(col) for col in df.columns]
    placeholders = ','.join(['%s'] * len(columns))
    col_list = ','.join([f'`{col}`' for col in columns])
    insert_sql = f"INSERT INTO `{safe_table}` ({col_list}) VALUES ({placeholders})"

    rows = []
    for _, row in df.iterrows():
        values = [None if pd.isna(row[col]) else row[col] for col in df.columns]
        rows.append(values)

    if rows:
        cursor.executemany(insert_sql, rows)
    return len(rows)


def save_processed_data_to_mariadb(data: Dict, conn_info: Dict[str, any], table_prefix: str = 'deposit_', overwrite: bool = False) -> Dict[str, int]:
    stats = {}
    with get_mariadb_connection(
        host=conn_info['host'],
        port=conn_info['port'],
        user=conn_info['user'],
        password=conn_info['password'],
        database=conn_info['database'],
    ) as conn:
        cursor = conn.cursor()
        for key, df in [
            ('comparison', data.get('comparison', pd.DataFrame())),
            ('summary_branch', data.get('summary_branch', pd.DataFrame())),
            ('summary_cust_type', data.get('summary_cust_type', pd.DataFrame())),
            ('summary_product', data.get('summary_product', pd.DataFrame())),
            ('segment_summary', data.get('segment_summary', pd.DataFrame())),
            ('alert_summary', data.get('alert_summary', pd.DataFrame())),
            ('recommendations', data.get('recommendations', pd.DataFrame())),
            ('driver_analysis', data.get('driver_analysis', pd.DataFrame())),
            ('prediction', data.get('prediction', pd.DataFrame())),
        ]:
            if df is not None and not df.empty:
                table_name = f"{table_prefix}{sanitize_sql_name(key)}"
                create_mariadb_table(cursor, table_name, df)
                inserted = write_dataframe_to_mariadb(cursor, table_name, df, overwrite=overwrite)
                stats[table_name] = inserted
        conn.commit()
    return stats


def render_friendly_error(error_text: str) -> None:
    """Display user-friendly validation errors."""
    st.error(f"❌ {error_text}")


def _safe_quantile(series: pd.Series, q: float, default_value: float) -> float:
    """Get quantile safely with fallback for empty/invalid series."""
    if series is None or series.empty:
        return default_value

    value = series.quantile(q)
    if pd.isna(value):
        return default_value

    return float(value)


def build_action_recommendations(comparison_df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Build rule-based customer action recommendations."""
    if comparison_df.empty:
        return pd.DataFrame(), {
            'risk_threshold': 0,
            'growth_threshold': 0,
            'new_open_threshold': 0,
        }

    negative_abs = comparison_df.loc[comparison_df['DELTA'] < 0, 'DELTA'].abs()
    positive_vals = comparison_df.loc[comparison_df['DELTA'] > 0, 'DELTA']
    new_open_vals = comparison_df.loc[comparison_df['BIEN_DONG'] == 'MO_MOI', 'TOTAL_T2']

    risk_threshold = max(50_000_000, _safe_quantile(negative_abs, 0.75, 50_000_000))
    growth_threshold = max(50_000_000, _safe_quantile(positive_vals, 0.75, 50_000_000))
    new_open_threshold = max(100_000_000, _safe_quantile(new_open_vals, 0.75, 100_000_000))

    rows = []
    for row in comparison_df.itertuples(index=False):
        priority = None
        action = None
        recommendation_group = None
        reason = None

        if row.BIEN_DONG == 'TAT_TOAN' and row.TOTAL_T1 > 0:
            priority = 'RAT_CAO'
            recommendation_group = 'GIU_CHAN'
            action = 'Lien he trong 48h, tim nguyen nhan tat toan va de xuat tai tuc.'
            reason = f'Tat toan toan bo {row.TOTAL_T1:,.0f}.'
        elif row.DELTA <= -1.5 * risk_threshold:
            priority = 'RAT_CAO'
            recommendation_group = 'GIU_CHAN'
            action = 'Uu tien cham soc ngay, de xuat goi lai suat/uu dai chuyen biet.'
            reason = f'Giam rat manh {row.DELTA:,.0f}, vuot nguong canh bao cao.'
        elif row.DELTA <= -risk_threshold:
            priority = 'CAO'
            recommendation_group = 'GIU_CHAN'
            action = 'Goi cham soc chu dong, xac minh nhu cau va de xuat san pham phu hop.'
            reason = f'Giam manh {row.DELTA:,.0f}, vuot nguong canh bao.'
        elif row.BIEN_DONG == 'MO_MOI' and row.TOTAL_T2 >= new_open_threshold:
            priority = 'TRUNG_BINH'
            recommendation_group = 'ONBOARDING'
            action = 'Onboarding va cross-sell san pham phu tro trong 7 ngay dau.'
            reason = f'Mo moi gia tri lon {row.TOTAL_T2:,.0f}.'
        elif row.TOTAL_T2 >= 200_000_000 and row.DELTA > 0:
            priority = 'TRUNG_BINH'
            recommendation_group = 'MO_RONG'
            action = 'Xem xet upsell/cross-sell san pham phu hop cho khach hang gia tri cao.'
            reason = f'Khach tang va co du lon {row.TOTAL_T2:,.0f}.'
        elif row.DELTA <= -risk_threshold and row.TOTAL_T2 >= 100_000_000:
            priority = 'CAO'
            recommendation_group = 'GIU_CHAN'
            action = 'Kiem tra chinh sach phi va uu dai giu chan khach hang gia tri cao.'
            reason = f'Giam manh {row.DELTA:,.0f} nhung van co du lon {row.TOTAL_T2:,.0f}.'
        elif row.DELTA >= growth_threshold:
            priority = 'TRUNG_BINH'
            recommendation_group = 'MO_RONG'
            action = 'Duy tri da tang truong, de xuat goi gia tri cao hon/VIP retention.'
            reason = f'Tang manh {row.DELTA:,.0f}.'

        if priority is not None:
            rows.append({
                'MUC_UU_TIEN': priority,
                'NHOM_KHUYEN_NGHI': recommendation_group,
                'HANH_DONG_GOI_Y': action,
                'LY_DO': reason,
                'MA_CN': row.MA_CN,
                'MA_KH': row.MA_KH,
                'TEN_KH': row.TEN_KH,
                'CUST_TYPE_NAME': row.CUST_TYPE_NAME,
                'TOTAL_T1': row.TOTAL_T1,
                'TOTAL_T2': row.TOTAL_T2,
                'DELTA': row.DELTA,
                'BIEN_DONG': row.BIEN_DONG,
                'ABS_DELTA': abs(row.DELTA),
                'DIEM_RUI_RO': getattr(row, 'CHURN_SCORE', 0),
            })

    if not rows:
        return pd.DataFrame(), {
            'risk_threshold': risk_threshold,
            'growth_threshold': growth_threshold,
            'new_open_threshold': new_open_threshold,
        }

    recommendations_df = pd.DataFrame(rows)
    if not recommendations_df.empty and 'MUC_UU_TIEN' in recommendations_df.columns:
        priority_order = {'RAT_CAO': 0, 'CAO': 1, 'TRUNG_BINH': 2}
        recommendations_df['priority_rank'] = recommendations_df['MUC_UU_TIEN'].map(priority_order).fillna(9)
        recommendations_df = recommendations_df.sort_values(
            ['priority_rank', 'ABS_DELTA'],
            ascending=[True, False],
        ).drop(columns=['priority_rank']).reset_index(drop=True)

    return recommendations_df, {
        'risk_threshold': risk_threshold,
        'growth_threshold': growth_threshold,
        'new_open_threshold': new_open_threshold,
    }


def calculate_risk_score(row: pd.Series) -> int:
    """Estimate a risk/churn score for a customer row."""
    if row['TOTAL_T1'] == 0:
        base = 30 if row['BIEN_DONG'] == 'MO_MOI' else 50
        return min(100, int(base))

    severity = abs(row['DELTA']) / max(row['TOTAL_T1'], 1)
    score = severity * 100
    if row['BIEN_DONG'] == 'TAT_TOAN':
        score += 30
    elif row['BIEN_DONG'] == 'GIAM':
        score += 20
    elif row['BIEN_DONG'] == 'MO_MOI':
        score += 10
    return min(100, int(round(score)))


def build_segment_summary(comparison_df: pd.DataFrame) -> pd.DataFrame:
    """Build a summary by customer balance bucket."""
    if comparison_df.empty:
        return pd.DataFrame()

    df = comparison_df.copy()
    labels = [bucket[0] for bucket in SEGMENT_BUCKETS]
    bins = [bucket[1] for bucket in SEGMENT_BUCKETS] + [SEGMENT_BUCKETS[-1][2]]
    df['BALANCE_BUCKET'] = pd.cut(
        df['TOTAL_T2'],
        bins=bins,
        labels=labels,
        right=False,
        include_lowest=True,
    ).astype(str)

    grouped = df.groupby('BALANCE_BUCKET', as_index=False).agg({
        'MA_KH': 'count',
        'TOTAL_T1': 'sum',
        'TOTAL_T2': 'sum',
        'DELTA': 'sum',
        'CHURN_SCORE': 'mean',
    }).rename(columns={
        'MA_KH': 'SO_KH',
        'TOTAL_T1': 'TONG_T1',
        'TOTAL_T2': 'TONG_T2',
        'DELTA': 'TONG_DELTA',
        'CHURN_SCORE': 'DIEM_RUI_RO_TRUNG_BINH',
    })

    grouped['TY_LE_TANG_TRUONG'] = grouped.apply(
        lambda r: (r['TONG_DELTA'] / r['TONG_T1'] * 100) if r['TONG_T1'] != 0 else 0,
        axis=1,
    )

    change_counts = df.groupby(['BALANCE_BUCKET', 'BIEN_DONG']).size().unstack(fill_value=0)
    for status in ['MO_MOI', 'TAT_TOAN', 'TANG', 'GIAM', 'KHONG_DOI']:
        if status in change_counts.columns:
            grouped[status] = change_counts[status].values
        else:
            grouped[status] = 0

    return grouped[['BALANCE_BUCKET', 'SO_KH', 'TONG_T1', 'TONG_T2', 'TONG_DELTA', 'TY_LE_TANG_TRUONG', 'MO_MOI', 'TAT_TOAN', 'TANG', 'GIAM', 'KHONG_DOI', 'DIEM_RUI_RO_TRUNG_BINH']]


def build_alert_summary(
    summary_branch: pd.DataFrame,
    summary_change: pd.DataFrame,
    outliers_df: pd.DataFrame,
    segment_summary: pd.DataFrame,
    recommendations_df: pd.DataFrame,
) -> pd.DataFrame:
    """Build a list of alerts for business review."""
    rows = []

    if not summary_branch.empty:
        for row in summary_branch.itertuples(index=False):
            if row.TONG_DELTA < 0 and row.TONG_DELTA <= -ALERT_BRANCH_DELTA_THRESHOLD:
                rows.append({
                    'LOAI_ALERT': 'Chi nhánh giảm mạnh',
                    'MA_CN': row.MA_CN,
                    'GIA_TRI': f"{row.TONG_DELTA:,.0f}",
                    'DIEN_GIAI': f"Chi nhánh {row.MA_CN} giảm {row.TONG_DELTA:,.0f} so với quý trước.",
                })
            elif row.TY_LE_TANG_TRUONG <= ALERT_BRANCH_DROP_RATE:
                rows.append({
                    'LOAI_ALERT': 'Tốc độ tăng trưởng thấp',
                    'MA_CN': row.MA_CN,
                    'GIA_TRI': f"{row.TY_LE_TANG_TRUONG:.2%}",
                    'DIEN_GIAI': f"Chi nhánh {row.MA_CN} có tỷ lệ tăng trưởng {row.TY_LE_TANG_TRUONG:.2%}.",
                })

    if not summary_change.empty:
        weak_segments = summary_change[summary_change['TONG_DELTA'] < 0]
        for row in weak_segments.itertuples(index=False):
            if abs(row.TONG_DELTA) >= ALERT_BRANCH_DELTA_THRESHOLD:
                rows.append({
                    'LOAI_ALERT': 'Nhóm biến động giảm lớn',
                    'MA_CN': '',
                    'GIA_TRI': f"{row.TONG_DELTA:,.0f}",
                    'DIEN_GIAI': f"Nhóm biến động {row.BIEN_DONG} giảm lớn với tổng DELTA {row.TONG_DELTA:,.0f}.",
                })

    if not outliers_df.empty:
        rows.append({
            'LOAI_ALERT': 'Phát hiện bất thường',
            'MA_CN': '',
            'GIA_TRI': len(outliers_df),
            'DIEN_GIAI': f"Có {len(outliers_df)} khách hàng bị phát hiện bất thường theo IQR.",
        })

    if not recommendations_df.empty and 'MUC_UU_TIEN' in recommendations_df.columns:
        high_risk = len(recommendations_df[recommendations_df['MUC_UU_TIEN'] == 'RAT_CAO'])
        if high_risk > 0:
            rows.append({
                'LOAI_ALERT': 'Rủi ro khách hàng cao',
                'MA_CN': '',
                'GIA_TRI': high_risk,
                'DIEN_GIAI': f"Có {high_risk} khách hàng ở mức ưu tiên RẤT CAO cần giải pháp giữ chân.",
            })

    if not segment_summary.empty:
        negative_bucket = segment_summary[segment_summary['TONG_DELTA'] < 0]
        if not negative_bucket.empty:
            worst_bucket = negative_bucket.sort_values('TONG_DELTA').iloc[0]
            rows.append({
                'LOAI_ALERT': 'Phân khúc giảm',
                'MA_CN': worst_bucket.BALANCE_BUCKET,
                'GIA_TRI': f"{worst_bucket.TONG_DELTA:,.0f}",
                'DIEN_GIAI': f"Phân khúc {worst_bucket.BALANCE_BUCKET} giảm {worst_bucket.TONG_DELTA:,.0f}.",
            })

    if not rows:
        return pd.DataFrame()

    alert_df = pd.DataFrame(rows)
    alert_df.index = range(1, len(alert_df) + 1)
    return alert_df[['LOAI_ALERT', 'MA_CN', 'GIA_TRI', 'DIEN_GIAI']]


def build_top_customers(comparison_df: pd.DataFrame, limit: int = 20) -> dict:
    """Build top gainers, top losers and top value customer tables."""
    if comparison_df.empty:
        return {
            'top_gainers': pd.DataFrame(),
            'top_losers': pd.DataFrame(),
            'top_value': pd.DataFrame(),
        }

    top_gainers = comparison_df.sort_values('DELTA', ascending=False).head(limit).copy()
    top_losers = comparison_df.sort_values('DELTA', ascending=True).head(limit).copy()
    top_value = comparison_df.sort_values('TOTAL_T2', ascending=False).head(limit).copy()

    for df in [top_gainers, top_losers, top_value]:
        for col in ['TOTAL_T1', 'TOTAL_T2', 'DELTA']:
            if col in df.columns:
                df[col] = df[col].astype(float)

    return {
        'top_gainers': top_gainers,
        'top_losers': top_losers,
        'top_value': top_value,
    }


def get_last_run_metrics() -> dict:
    """Read the last two history records and return summary comparison."""
    history_df = load_history(limit=2)
    if len(history_df) < 2:
        return {}

    current = history_df.iloc[0]
    previous = history_df.iloc[1]
    return {
        'current': current,
        'previous': previous,
        'delta_customers': int(current['customers'] - previous['customers']) if 'customers' in current and 'customers' in previous else None,
        'delta_total': float(current['total_delta'] - previous['total_delta']) if 'total_delta' in current and 'total_delta' in previous else None,
    }


def build_change_type_trends(comparison_df: pd.DataFrame) -> pd.DataFrame:
    """Build trend counts by change type for dashboard charts."""
    if comparison_df.empty:
        return pd.DataFrame()

    trends = comparison_df.groupby('BIEN_DONG', as_index=False).agg({
        'MA_KH': 'count',
        'DELTA': 'sum'
    }).rename(columns={
        'MA_KH': 'SO_KH',
        'DELTA': 'TONG_DELTA'
    })
    return trends.sort_values('SO_KH', ascending=False)


def format_money(value) -> str:
    if pd.isna(value):
        return '0'
    return f"{value:,.0f}"


def build_driver_table(summary_df: pd.DataFrame, group_col: str, analysis_group: str) -> pd.DataFrame:
    """Build driver contribution table from summary data."""
    if summary_df.empty or group_col not in summary_df.columns:
        return pd.DataFrame()

    driver_df = summary_df[[group_col, 'TONG_DELTA']].copy()
    driver_df = driver_df.rename(columns={group_col: 'NHOM'})

    net_total = float(driver_df['TONG_DELTA'].sum())
    abs_total = float(driver_df['TONG_DELTA'].abs().sum())

    if net_total != 0:
        driver_df['DONG_GOP_RONG_%'] = driver_df['TONG_DELTA'] / net_total * 100
    else:
        driver_df['DONG_GOP_RONG_%'] = 0.0

    if abs_total != 0:
        driver_df['DONG_GOP_ABS_%'] = driver_df['TONG_DELTA'].abs() / abs_total * 100
    else:
        driver_df['DONG_GOP_ABS_%'] = 0.0

    driver_df['XU_HUONG'] = driver_df['TONG_DELTA'].apply(
        lambda value: 'TANG' if value > 0 else ('GIAM' if value < 0 else 'TRUNG_TINH')
    )
    driver_df['NHOM_PHAN_TICH'] = analysis_group
    driver_df['ABS_DELTA'] = driver_df['TONG_DELTA'].abs()

    return driver_df[[
        'NHOM_PHAN_TICH',
        'NHOM',
        'TONG_DELTA',
        'DONG_GOP_RONG_%',
        'DONG_GOP_ABS_%',
        'XU_HUONG',
        'ABS_DELTA',
    ]].sort_values('ABS_DELTA', ascending=False).reset_index(drop=True)


def build_predictive_forecast(summary_branch: pd.DataFrame) -> pd.DataFrame:
    """Build a practical forecast using two-period momentum and scenario envelopes."""
    if summary_branch.empty or not {'TONG_T1', 'TONG_T2'}.issubset(summary_branch.columns):
        return pd.DataFrame()

    forecast = summary_branch[['MA_CN', 'TONG_T1', 'TONG_T2', 'TONG_DELTA']].copy()
    forecast['MOMENTUM'] = forecast.apply(
        lambda row: (row['TONG_T2'] - row['TONG_T1']) / max(abs(row['TONG_T1']), 1),
        axis=1
    )
    forecast['PREDICT_T3_BASE'] = forecast['TONG_T2'] + (forecast['TONG_T2'] - forecast['TONG_T1'])
    forecast['PREDICT_T3_OPT'] = forecast['TONG_T2'] + (forecast['TONG_T2'] - forecast['TONG_T1']) * 1.25
    forecast['PREDICT_T3_PESS'] = forecast['TONG_T2'] + (forecast['TONG_T2'] - forecast['TONG_T1']) * 0.6
    forecast['BASE_DELTA'] = forecast['PREDICT_T3_BASE'] - forecast['TONG_T2']
    forecast['OPT_DELTA'] = forecast['PREDICT_T3_OPT'] - forecast['TONG_T2']
    forecast['PESS_DELTA'] = forecast['PREDICT_T3_PESS'] - forecast['TONG_T2']
    forecast['CONFIDENCE'] = forecast['MOMENTUM'].abs().apply(
        lambda x: 'Cao' if x >= 0.30 else ('Trung bình' if x >= 0.10 else 'Thấp')
    )
    forecast['FORECAST_DIRECTION'] = forecast['BASE_DELTA'].apply(
        lambda x: 'TĂNG' if x > 0 else ('GIẢM' if x < 0 else 'ỔN ĐỊNH')
    )
    forecast['RISK_NOTE'] = forecast.apply(
        lambda row: 'Đang mất động lực, xem xét chiến lược giữ chân' if row['BASE_DELTA'] < 0 else
                    ('Tiếp tục đẩy mạnh sản phẩm hiện tại' if row['BASE_DELTA'] > 0 else 'Duy trì và theo dõi chặt'),
        axis=1
    )
    return forecast.sort_values('BASE_DELTA', ascending=True).reset_index(drop=True)


def normalize_forecast_columns(forecast: pd.DataFrame) -> pd.DataFrame:
    """Ensure forecast data has required derived columns for display."""
    if forecast.empty:
        return forecast

    df = forecast.copy()
    if 'PREDICT_T3_BASE' not in df.columns and {'TONG_T1', 'TONG_T2'}.issubset(df.columns):
        df['PREDICT_T3_BASE'] = df['TONG_T2'] + (df['TONG_T2'] - df['TONG_T1'])
    if 'BASE_DELTA' not in df.columns and {'PREDICT_T3_BASE', 'TONG_T2'}.issubset(df.columns):
        df['BASE_DELTA'] = df['PREDICT_T3_BASE'] - df['TONG_T2']
    if 'PREDICT_T3_OPT' not in df.columns and {'TONG_T1', 'TONG_T2'}.issubset(df.columns):
        df['PREDICT_T3_OPT'] = df['TONG_T2'] + (df['TONG_T2'] - df['TONG_T1']) * 1.25
    if 'PREDICT_T3_PESS' not in df.columns and {'TONG_T1', 'TONG_T2'}.issubset(df.columns):
        df['PREDICT_T3_PESS'] = df['TONG_T2'] + (df['TONG_T2'] - df['TONG_T1']) * 0.6
    if 'OPT_DELTA' not in df.columns and {'PREDICT_T3_OPT', 'TONG_T2'}.issubset(df.columns):
        df['OPT_DELTA'] = df['PREDICT_T3_OPT'] - df['TONG_T2']
    if 'PESS_DELTA' not in df.columns and {'PREDICT_T3_PESS', 'TONG_T2'}.issubset(df.columns):
        df['PESS_DELTA'] = df['PREDICT_T3_PESS'] - df['TONG_T2']
    if 'MOMENTUM' not in df.columns and {'TONG_T1', 'TONG_T2'}.issubset(df.columns):
        df['MOMENTUM'] = df.apply(
            lambda row: (row['TONG_T2'] - row['TONG_T1']) / max(abs(row['TONG_T1']), 1),
            axis=1
        )
    if 'CONFIDENCE' not in df.columns and 'MOMENTUM' in df.columns:
        df['CONFIDENCE'] = df['MOMENTUM'].abs().apply(
            lambda x: 'Cao' if x >= 0.30 else ('Trung bình' if x >= 0.10 else 'Thấp')
        )
    if 'FORECAST_DIRECTION' not in df.columns and 'BASE_DELTA' in df.columns:
        df['FORECAST_DIRECTION'] = df['BASE_DELTA'].apply(
            lambda x: 'TĂNG' if x > 0 else ('GIẢM' if x < 0 else 'ỔN ĐỊNH')
        )
    if 'RISK_NOTE' not in df.columns and 'BASE_DELTA' in df.columns:
        df['RISK_NOTE'] = df.apply(
            lambda row: 'Đang mất động lực, xem xét chiến lược giữ chân' if row['BASE_DELTA'] < 0 else
                        ('Tiếp tục đẩy mạnh sản phẩm hiện tại' if row['BASE_DELTA'] > 0 else 'Duy trì và theo dõi chặt'),
            axis=1
        )
    return df


def build_ai_insights(data: Dict) -> List[str]:
    """Generate simple AI-style insights based on analysis data."""
    comparison_df = data.get('comparison', pd.DataFrame())
    alert_summary = data.get('alert_summary', pd.DataFrame())
    prediction = data.get('prediction', pd.DataFrame())

    insights = []
    if comparison_df.empty:
        return insights

    total_delta = float(comparison_df['DELTA'].sum())
    if total_delta > 0:
        insights.append(f"Tổng DELTA tích cực: {total_delta:,.0f}. Xu hướng thị trường hiện đang tăng.")
    elif total_delta < 0:
        insights.append(f"Tổng DELTA âm: {total_delta:,.0f}. Thị trường đang bị kéo xuống, cần tập trung giữ chân khách hàng." )
    else:
        insights.append("Tổng DELTA gần bằng 0, thị trường đang ổn định nhưng vẫn cần theo dõi các biến động nhỏ.")

    top_branch = data['summary_branch'].sort_values('TONG_DELTA', ascending=False).head(1)
    if not top_branch.empty:
        row = top_branch.iloc[0]
        insights.append(f"Chi nhánh đang dẫn đầu tăng trưởng: {row['MA_CN']} với DELTA {row['TONG_DELTA']:,.0f}.")

    if not alert_summary.empty:
        insights.append(f"Đang có {len(alert_summary)} cảnh báo quan trọng cần xử lý ngay.")

    if not prediction.empty:
        bad_forecast = prediction[prediction['FORECAST_DIRECTION'] == 'GIẢM']
        good_forecast = prediction[prediction['FORECAST_DIRECTION'] == 'TĂNG']
        if len(bad_forecast) > 0:
            insights.append(f"{len(bad_forecast)} chi nhánh dự báo giảm vòng tới, cần ưu tiên giữ chân.")
        if len(good_forecast) > 0:
            insights.append(f"{len(good_forecast)} chi nhánh dự báo tăng, có thể mở rộng sản phẩm/tài trợ.")

    top_clients = data.get('top_customers', {}).get('top_gainers', pd.DataFrame())
    if not top_clients.empty:
        best = top_clients.iloc[0]
        insights.append(f"Khách hàng tăng mạnh nhất: {best.get('TEN_KH', 'N/A')} với DELTA {best.get('DELTA', 0):,.0f}.")

    # Strategy recommendation summary
    recommendations_df = data.get('recommendations', pd.DataFrame())
    if not recommendations_df.empty and 'MUC_UU_TIEN' in recommendations_df.columns:
        high_risk = len(recommendations_df[recommendations_df['MUC_UU_TIEN'] == 'RAT_CAO'])
        if high_risk > 0:
            insights.append(f"Có {high_risk} khách hàng ưu tiên RẤT CAO cần xử lý trong 48h.")

    if not data.get('segment_summary', pd.DataFrame()).empty:
        worst_segment = data['segment_summary'].sort_values('TONG_DELTA').head(1)
        if not worst_segment.empty:
            detail = worst_segment.iloc[0]
            insights.append(f"Phân khúc {detail['BALANCE_BUCKET']} đang giảm mạnh, cần rà soát chính sách chăm sóc.")

    return insights


def build_market_context(data: Dict) -> List[str]:
    comparison_df = data.get('comparison', pd.DataFrame())
    summary_branch = data.get('summary_branch', pd.DataFrame())
    summary_product = data.get('summary_product', pd.DataFrame())
    segment_summary = data.get('segment_summary', pd.DataFrame())

    if comparison_df.empty:
        return [
            "Chưa có dữ liệu đủ để xác định bối cảnh thị trường hiện tại.",
            "Vui lòng hoàn thành bước so sánh để nhận định xu hướng vốn và thị trường." 
        ]

    total_delta = float(comparison_df['DELTA'].sum())
    total_t1 = float(comparison_df['TOTAL_T1'].sum())
    total_t2 = float(comparison_df['TOTAL_T2'].sum())
    branch_up = len(summary_branch[summary_branch['TONG_DELTA'] > 0]) if not summary_branch.empty else 0
    branch_down = len(summary_branch[summary_branch['TONG_DELTA'] < 0]) if not summary_branch.empty else 0
    positive_product = summary_product.sort_values('TONG_DELTA', ascending=False).head(2)
    negative_product = summary_product.sort_values('TONG_DELTA').head(2)
    worst_segment = segment_summary.sort_values('TONG_DELTA').head(1) if not segment_summary.empty else pd.DataFrame()

    market_situation = 'TĂNG' if total_delta > 0 else ('GIẢM' if total_delta < 0 else 'ỔN ĐỊNH')
    growth_rate = (total_delta / max(abs(total_t1), 1))

    context = [
        "Dữ liệu T1/T2 đã phản ánh bối cảnh thị trường tiền gửi hiện tại, bao gồm xu hướng dòng vốn, mức độ cạnh tranh lãi suất và hành vi khách hàng.",
        f"Tổng tiền gửi T1: {total_t1:,.0f}, T2: {total_t2:,.0f}, DELTA: {total_delta:,.0f}. Thị trường nội bộ đang có xu hướng {market_situation.lower()} với tốc độ biến động {growth_rate:.2%}.",
        f"Có {branch_up} chi nhánh tăng trưởng và {branch_down} chi nhánh chịu áp lực giảm. Đây là tín hiệu quan trọng để xác định vùng cần huy động vốn và giữ chân khách hàng.",
    ]

    if not positive_product.empty:
        products = ", ".join([str(x) for x in positive_product['DP_GROUP'].tolist()])
        context.append(
            f"Sản phẩm tăng trưởng tốt hiện tại: {products}. Đây là những nhóm sản phẩm có thể được đẩy mạnh trong chiến lược huy động vốn để tận dụng xu hướng thị trường."
        )
    if not negative_product.empty:
        products = ", ".join([str(x) for x in negative_product['DP_GROUP'].tolist()])
        context.append(
            f"Sản phẩm suy yếu cần tái cấu trúc: {products}. Nên xem xét gói lãi suất mới, chương trình khuyến mại hoặc kết hợp với sản phẩm phái sinh để thu hút vốn trở lại."
        )
    if not worst_segment.empty:
        detail = worst_segment.iloc[0]
        context.append(
            f"Phân khúc có biến động tiêu cực nhất hiện nay là {detail['BALANCE_BUCKET']} với DELTA {detail['TONG_DELTA']:,.0f}. Phải có giải pháp giữ chân và gia tăng tỷ lệ tiền gửi ổn định cho phân khúc này."
        )

    context.append(
        "Trong bối cảnh thị trường cạnh tranh hiện tại, nguồn vốn ưu tiên thu hút là tiền gửi kỳ hạn linh hoạt, ưu đãi lãi suất và các gói cộng điểm cho khách hàng mới/toàn phần."
    )
    context.append(
        "Thị trường hiện đang phản ánh nhu cầu khách hàng dịch chuyển sang sản phẩm có giá trị gia tăng: tiết kiệm online, ưu đãi lãi suất cố định và gói kết hợp đầu tư/bảo hiểm."
    )

    # Add interest rate benchmark insights
    interest_insights = get_interest_rate_insights(5.5)  # Assume 5.5% internal average
    context.extend(interest_insights)

    # Add AI-powered insights
    try:
        # Get customer data for AI analysis
        customer_data = data.get('customer_data', pd.DataFrame())
        if not customer_data.empty:
            # Customer segmentation
            segmentation = perform_customer_segmentation(customer_data)
            if 'insights' in segmentation:
                context.append("\n" + segmentation['insights'])

            # Churn risk analysis
            churn_analysis = predict_churn_risk(customer_data)
            if 'insights' in churn_analysis:
                context.append("\n" + churn_analysis['insights'])

            # AI recommendations
            recommendations = generate_ai_recommendations(customer_data)
            context.append("\n" + recommendations)
    except Exception as e:
        context.append(f"\n⚠️ Không thể tạo insights AI: {str(e)}")

    return context


def build_capital_strategy(data: Dict) -> List[Dict[str, str]]:
    comparison_df = data.get('comparison', pd.DataFrame())
    summary_branch = data.get('summary_branch', pd.DataFrame())
    summary_product = data.get('summary_product', pd.DataFrame())
    segment_summary = data.get('segment_summary', pd.DataFrame())

    total_delta = float(comparison_df['DELTA'].sum()) if not comparison_df.empty else 0
    is_negative_market = total_delta < 0
    strategies = []

    strategies.append({
        'title': '1. Giữ chân khách hàng có DELTA âm lớn',
        'description': (
            "- Ưu tiên tiếp cận ngay lập tức các khách hàng giảm mạnh, đặc biệt nhóm tất toán và giảm > ngưỡng nguy cơ. "
            "- Triển khai chương trình chăm sóc cao cấp, miễn phí chuyển tiền, tặng quà hoặc nâng cấp lãi suất cho kỳ hạn tiếp theo. "
            "- Giao cho đội chuyên trách phụ trách giữ chân nhóm này, cam kết phản hồi trong 24-48 tiếng."
        )
    })

    strategies.append({
        'title': '2. Triển khai giải pháp huy động vốn cho khách hàng mới và mở mới',
        'description': (
            "- Dùng dữ liệu MO_MOI để xác định khách hàng mở mới giá trị cao và tặng ưu đãi lãi suất chào mừng. "
            "- Thiết kế gói sản phẩm tiền gửi kết hợp dịch vụ số, ưu đãi phí và trao đổi thông tin qua kênh online để rút ngắn thời gian onboarding. "
            "- Áp dụng cơ chế thẩm định nhanh, hỗ trợ tư vấn 1-1 cho khách hàng có tổng tài sản lớn."
        )
    })

    strategies.append({
        'title': '3. Tập trung sản phẩm tốt nhất theo xu hướng thị trường',
        'description': (
            "- Đẩy mạnh các sản phẩm có DELTA tích cực, tận dụng sức hút của nhóm sản phẩm này để thu hút vốn mới. "
            "- Với sản phẩm suy yếu, kiểm tra lại chính sách lãi suất, kỳ hạn, điều kiện chuyển đổi và truyền thông. "
            "- Khuyến nghị các gói tiết kiệm kỳ hạn 6-12 tháng, kết hợp quà tặng hoặc nâng mức lãi suất nếu khách hàng gửi thêm."
        )
    })

    strategies.append({
        'title': '4. Chiến lược vốn theo chi nhánh và phân khúc',
        'description': (
            "- Xác định chi nhánh có áp lực giảm mạnh và tăng cường hỗ trợ nguồn lực, thưởng KPI cho huy động vốn. "
            "- Với chi nhánh tăng trưởng tốt, mở rộng gói ưu đãi cho khách hàng có DELTA cao để dòng vốn giữ được ổn định. "
            "- Phân tích sâu phân khúc <50M, 50-200M, 200-500M, >500M và xây dựng chương trình riêng cho từng nhóm."
        )
    })

    strategies.append({
        'title': '5. Chủ động phản ánh thị trường hiện tại',
        'description': (
            "- Nếu thị trường đang giảm tổng DELTA, cần tăng cường thông điệp giữ chân và ưu đãi lãi suất để bù đắp nguồn vốn bị rút ra. "
            "- Nếu thị trường đang tăng, ưu tiên giữ nhịp tăng trưởng bằng cách giới thiệu gói chuyển tiền linh hoạt, gói tích lũy lãi suất cao. "
            "- Luôn phản hồi thông tin thị trường qua các báo cáo hàng tuần, cập nhật biến động lãi suất và đối thủ cạnh tranh."
        )
    })

    if is_negative_market:
        strategies.append({
            'title': '6. Giải pháp gia tăng vốn trong thị trường áp lực',
            'description': (
                "- Triển khai chương trình ưu đãi lãi suất ngắn hạn + gói quà tặng cho khách hàng chuyển đổi sang gửi tiền kỳ hạn dài. "
                "- Khuyến khích khách hàng gửi thêm bằng cơ chế thưởng lũy tiến, cộng thêm lãi suất cho số tiền gửi mới. "
                "- Tập trung vào sản phẩm thanh khoản cao, giải pháp tiền gửi linh hoạt để khách hàng yên tâm lưu giữ vốn."
            )
        })
    else:
        strategies.append({
            'title': '6. Giải pháp mở rộng huy động vốn khi thị trường đang thuận lợi',
            'description': (
                "- Kéo dài hiệu quả tăng trưởng bằng các chương trình khách hàng thân thiết, ưu đãi mở rộng hạn mức gửi. "
                "- Phát triển thêm các gói sản phẩm tích hợp gửi tiết kiệm + đầu tư / bảo hiểm để tăng lượng vốn tại khách hàng hiện hữu. "
                "- Tăng tốc marketing vào phân khúc có delta dương mạnh để tận dụng dư địa thị trường."
            )
        })

    strategies.append({
        'title': '7. Huy động vốn và chăm sóc đồng bộ',
        'description': (
            "- Liên kết đội kinh doanh, chăm sóc và sản phẩm để triển khai chiến dịch huy động vốn đồng bộ. "
            "- Dùng dữ liệu so sánh T1-T2 để làm căn cứ cho kịch bản hành động, báo cáo thị trường và đề xuất ưu đãi. "
            "- Định kỳ đo lường hiệu quả từng chiến dịch và điều chỉnh dựa trên kết quả thực tế."
        )
    })

    return strategies


def extract_action_insight_cards(data: Dict) -> List[Dict[str, str]]:
    """Generate a short set of action cards for AI insights."""
    cards = []
    comparison_df = data.get('comparison', pd.DataFrame())
    forecast = data.get('prediction', pd.DataFrame())
    recommendations = data.get('recommendations', pd.DataFrame())

    if not comparison_df.empty:
        total_delta = float(comparison_df['DELTA'].sum())
        cards.append({
            'title': 'Tổng trạng',
            'message': f"Tổng DELTA hiện tại {total_delta:,.0f}. {'Tăng trưởng tích cực' if total_delta > 0 else 'Cần chú ý nếu giảm' if total_delta < 0 else 'Ổn định'}.",
            'type': 'summary'
        })

    if not forecast.empty:
        risk_count = len(forecast[forecast['FORECAST_DIRECTION'] == 'GIẢM'])
        opp_count = len(forecast[forecast['FORECAST_DIRECTION'] == 'TĂNG'])
        cards.append({
            'title': 'Dự báo chi nhánh',
            'message': f"{risk_count} chi nhánh có xu hướng giảm và {opp_count} chi nhánh có xu hướng tăng trong kỳ tới.",
            'type': 'forecast'
        })

    if not recommendations.empty and 'MUC_UU_TIEN' in recommendations.columns:
        urgent = len(recommendations[recommendations['MUC_UU_TIEN'] == 'RAT_CAO'])
        cards.append({
            'title': 'Hành động ưu tiên',
            'message': f"Có {urgent} khách hàng cần ưu tiên xử lý ngay để giảm thiểu rủi ro mất tiền.",
            'type': 'action'
        })

    return cards


def export_custom_report_to_excel(data: Dict, selected_sections: List[str]) -> bytes:
    """Export selected report sections to Excel."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        if 'Dashboard' in selected_sections:
            metrics = [
                ('Tổng khách hàng', len(data['comparison'])),
                ('Tổng T1', format_money(data['summary_branch']['TONG_T1'].sum())),
                ('Tổng T2', format_money(data['summary_branch']['TONG_T2'].sum())),
                ('Tổng DELTA', format_money(data['summary_branch']['TONG_DELTA'].sum())),
            ]
            pd.DataFrame(metrics, columns=['Chỉ số', 'Giá trị']).to_excel(writer, sheet_name='Dashboard', index=False)

        if 'Customer details' in selected_sections and not data['comparison'].empty:
            data['comparison'].to_excel(writer, sheet_name='ChiTietKhachHang', index=False)

        if 'Branch summary' in selected_sections and not data['summary_branch'].empty:
            data['summary_branch'].to_excel(writer, sheet_name='TheoChiNhanh', index=False)

        if 'Customer type' in selected_sections and not data['summary_cust_type'].empty:
            data['summary_cust_type'].to_excel(writer, sheet_name='TheoPhanKhuc', index=False)

        if 'Product summary' in selected_sections and not data['summary_product'].empty:
            data['summary_product'].to_excel(writer, sheet_name='TheoSanPham', index=False)

        if 'Segment analysis' in selected_sections and not data.get('segment_summary', pd.DataFrame()).empty:
            data['segment_summary'].to_excel(writer, sheet_name='PhanKhuc', index=False)

        if 'Market context' in selected_sections and data.get('market_context'):
            pd.DataFrame({'Nội dung': data['market_context']}).to_excel(writer, sheet_name='MarketContext', index=False)

        if 'Capital strategy' in selected_sections and data.get('capital_strategy'):
            pd.DataFrame(data['capital_strategy']).to_excel(writer, sheet_name='CapitalStrategy', index=False)

        if 'Alerts' in selected_sections and not data.get('alert_summary', pd.DataFrame()).empty:
            data['alert_summary'].to_excel(writer, sheet_name='CanhBao', index=False)

        if 'Recommendations' in selected_sections and not data.get('recommendations', pd.DataFrame()).empty:
            data['recommendations'].to_excel(writer, sheet_name='KhuyenNghi', index=False)

        if 'Predictive' in selected_sections and not data.get('prediction', pd.DataFrame()).empty:
            data['prediction'].to_excel(writer, sheet_name='DuBao', index=False)

        if 'AI Insights' in selected_sections and data.get('ai_insights'):
            pd.DataFrame({'Insight': data['ai_insights']}).to_excel(writer, sheet_name='AIInsights', index=False)

        if 'Charts' in selected_sections:
            chart_sources = {
                'Branch growth': data.get('summary_branch', pd.DataFrame()),
                'Customer type data': data.get('summary_cust_type', pd.DataFrame()),
                'Product group data': data.get('summary_product', pd.DataFrame()),
                'Change distribution': data.get('summary_change', pd.DataFrame()),
            }
            for sheet_name, df in chart_sources.items():
                if df is not None and not df.empty:
                    df.to_excel(writer, sheet_name=sheet_name, index=False)

    output.seek(0)
    return output.getvalue()


def tab_dashboard(data: Dict) -> None:
    """Render main dashboard with key charts and insights."""
    st.header('📊 Dashboard Tổng quan')

    comparison_df = data.get('comparison', pd.DataFrame())
    summary_branch = data.get('summary_branch', pd.DataFrame())

    if comparison_df.empty:
        st.info('Chưa có dữ liệu so sánh để hiển thị dashboard.')
        return

    # Key charts row
    col1, col2 = st.columns(2)

    with col1:
        # Branch performance chart
        if not summary_branch.empty and 'TONG_DELTA' in summary_branch.columns:
            fig_branch = px.bar(
                summary_branch.head(10),
                x='MA_CN',
                y='TONG_DELTA',
                title='Top 10 Chi nhánh theo DELTA',
                color='TONG_DELTA',
                color_continuous_scale='RdYlGn'
            )
            fig_branch.update_layout(height=400)
            st.plotly_chart(fig_branch, use_container_width=True)

    with col2:
        # Customer change distribution
        if 'BIEN_DONG' in comparison_df.columns:
            change_counts = comparison_df['BIEN_DONG'].value_counts()
            fig_change = px.pie(
                values=change_counts.values,
                names=change_counts.index,
                title='Phân bố biến động khách hàng'
            )
            fig_change.update_layout(height=400)
            st.plotly_chart(fig_change, use_container_width=True)

    st.divider()

    # Growth trends
    col3, col4 = st.columns(2)

    with col3:
        # Balance distribution
        if 'TOTAL_T2' in comparison_df.columns:
            fig_balance = px.histogram(
                comparison_df,
                x='TOTAL_T2',
                nbins=50,
                title='Phân bố số dư T2',
                marginal='box'
            )
            fig_balance.update_layout(height=350)
            st.plotly_chart(fig_balance, use_container_width=True)

    with col4:
        # Growth rate by branch
        if not summary_branch.empty and {'TONG_T1', 'TONG_T2'}.issubset(summary_branch.columns):
            summary_branch_copy = summary_branch.copy()
            summary_branch_copy['GROWTH_RATE'] = (
                (summary_branch_copy['TONG_T2'] - summary_branch_copy['TONG_T1']) /
                summary_branch_copy['TONG_T1'].clip(lower=1) * 100
            )
            fig_growth = px.bar(
                summary_branch_copy.head(10),
                x='MA_CN',
                y='GROWTH_RATE',
                title='Tỷ lệ tăng trưởng theo chi nhánh (%)',
                color='GROWTH_RATE',
                color_continuous_scale='RdYlGn'
            )
            fig_growth.update_layout(height=350)
            st.plotly_chart(fig_growth, use_container_width=True)


def tab_customer_details(data: Dict) -> None:
    """Display customer-level comparison details."""
    st.header('📋 Chi tiết khách hàng')
    comparison_df = data.get('comparison', pd.DataFrame())
    if comparison_df.empty:
        placeholder = st.container(key='info_no_customer_data')
        placeholder.info('Chưa có dữ liệu khách hàng để hiển thị. Vui lòng chạy so sánh trước.')
        return

    comparison_df = comparison_df.copy()
    comparison_df['DELTA'] = comparison_df['DELTA'].fillna(0)
    comparison_df['TOTAL_T1'] = comparison_df.get('TOTAL_T1', 0)
    comparison_df['TOTAL_T2'] = comparison_df.get('TOTAL_T2', 0)

    branches = sorted(comparison_df['MA_CN'].dropna().unique().tolist()) if 'MA_CN' in comparison_df.columns else []
    customer_types = sorted(comparison_df['CUST_TYPE_NAME'].dropna().unique().tolist()) if 'CUST_TYPE_NAME' in comparison_df.columns else []
    change_types = sorted(comparison_df['BIEN_DONG'].dropna().unique().tolist()) if 'BIEN_DONG' in comparison_df.columns else []

    with st.expander('Bộ lọc khách hàng', expanded=True):
        col1, col2, col3 = st.columns(3)
        selected_branch = col1.selectbox('Chi nhánh', options=['Tất cả'] + branches, index=0)
        selected_cust_type = col2.selectbox('Phân khúc khách hàng', options=['Tất cả'] + customer_types, index=0)
        selected_change_type = col3.selectbox('Loại biến động', options=['Tất cả'] + change_types, index=0)

    filtered_df = comparison_df
    if selected_branch != 'Tất cả':
        filtered_df = filtered_df[filtered_df['MA_CN'] == selected_branch]
    if selected_cust_type != 'Tất cả':
        filtered_df = filtered_df[filtered_df['CUST_TYPE_NAME'] == selected_cust_type]
    if selected_change_type != 'Tất cả':
        filtered_df = filtered_df[filtered_df['BIEN_DONG'] == selected_change_type]

    if filtered_df.empty:
        st.warning('Không có khách hàng phù hợp với bộ lọc đã chọn.')
        return

    st.metric('Tổng khách hàng', len(filtered_df))
    st.metric('Tổng DELTA', f"{filtered_df['DELTA'].sum():,.0f}")
    if 'TOTAL_T1' in filtered_df.columns:
        st.metric('Tổng T1', f"{filtered_df['TOTAL_T1'].sum():,.0f}")
    if 'TOTAL_T2' in filtered_df.columns:
        st.metric('Tổng T2', f"{filtered_df['TOTAL_T2'].sum():,.0f}")

    display_columns = [
         'MA_CN','MA_KH', 'TEN_KH', 'CUST_TYPE_NAME', 'DP_TYPE_CODE',
        'TOTAL_T1', 'TOTAL_T2', 'DELTA', 'BIEN_DONG', 'CHURN_SCORE', 'CHURN_RISK'
    ]
    display_columns = [col for col in display_columns if col in filtered_df.columns]
    if not display_columns:
        display_columns = filtered_df.columns.tolist()

    st.subheader('Danh sách khách hàng')
    st.dataframe(filtered_df[display_columns].sort_values(by='DELTA', ascending=True), use_container_width=True, height=420)

    with st.expander('Top 10 khách hàng giảm mạnh nhất'): 
        top_losers = filtered_df.nsmallest(10, 'DELTA') if 'DELTA' in filtered_df.columns else filtered_df.head(10)
        st.table(top_losers[display_columns].head(10))

    with st.expander('Top 10 khách hàng tăng mạnh nhất'):
        top_winners = filtered_df.nlargest(10, 'DELTA') if 'DELTA' in filtered_df.columns else filtered_df.head(10)
        st.table(top_winners[display_columns].head(10))

    # Add Excel export functionality
    if st.button('📊 Xuất Excel', key='export_customer_details', help='Xuất dữ liệu khách hàng ra file Excel'):
        try:
            # Create Excel export directly
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                # Export main customer data
                filtered_df[display_columns].to_excel(writer, sheet_name='Chi tiết khách hàng', index=False)
                
                # Export top losers
                top_losers[display_columns].head(10).to_excel(writer, sheet_name='Top giảm mạnh', index=False)
                
                # Export top winners  
                top_winners[display_columns].head(10).to_excel(writer, sheet_name='Top tăng mạnh', index=False)
                
                # Export summary
                summary_data = {
                    'Metric': ['Tổng khách hàng', 'Tổng DELTA', 'Tổng T1', 'Tổng T2'],
                    'Value': [
                        len(filtered_df),
                        filtered_df['DELTA'].sum() if 'DELTA' in filtered_df.columns else 0,
                        filtered_df['TOTAL_T1'].sum() if 'TOTAL_T1' in filtered_df.columns else 0,
                        filtered_df['TOTAL_T2'].sum() if 'TOTAL_T2' in filtered_df.columns else 0,
                    ]
                }
                pd.DataFrame(summary_data).to_excel(writer, sheet_name='Tóm tắt', index=False)
            
            excel_data = output.getvalue()
            st.download_button(
                label="📥 Tải file Excel",
                data=excel_data,
                file_name=f"customer_details_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key='download_customer_excel'
            )
        except Exception as e:
            st.error(f'Lỗi xuất Excel: {e}')


def tab_branch_summary(data: Dict) -> None:
    """Display branch-level summary."""
    st.header('🏢 Tóm tắt theo Chi nhánh')
    
    summary_branch = data.get('summary_branch', pd.DataFrame())
    if summary_branch.empty:
        st.info('Chưa có dữ liệu tóm tắt chi nhánh.')
        return
    
    # Key metrics
    total_branches = len(summary_branch)
    total_delta = summary_branch['TONG_DELTA'].sum() if 'TONG_DELTA' in summary_branch.columns else 0
    total_t1 = summary_branch['TONG_T1'].sum() if 'TONG_T1' in summary_branch.columns else 0
    total_t2 = summary_branch['TONG_T2'].sum() if 'TONG_T2' in summary_branch.columns else 0
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric('Tổng chi nhánh', total_branches)
    col2.metric('Tổng DELTA', f'{total_delta:,.0f}')
    col3.metric('Tổng T1', f'{total_t1:,.0f}')
    col4.metric('Tổng T2', f'{total_t2:,.0f}')
    
    # Branch table
    display_cols = ['MA_CN', 'SO_KH', 'TONG_T1', 'TONG_T2', 'TONG_DELTA', 'TY_LE_TANG_TRUONG']
    display_cols = [col for col in display_cols if col in summary_branch.columns]
    
    st.subheader('Chi tiết từng chi nhánh')
    st.dataframe(summary_branch[display_cols].sort_values('TONG_DELTA', ascending=False), use_container_width=True)
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        if 'TONG_DELTA' in summary_branch.columns:
            fig_delta = px.bar(
                summary_branch.sort_values('TONG_DELTA', ascending=False).head(15),
                x='MA_CN',
                y='TONG_DELTA',
                title='DELTA theo chi nhánh',
                color='TONG_DELTA',
                color_continuous_scale='RdYlGn'
            )
            st.plotly_chart(fig_delta, use_container_width=True)
    
    with col2:
        if 'TY_LE_TANG_TRUONG' in summary_branch.columns:
            fig_growth = px.bar(
                summary_branch.sort_values('TY_LE_TANG_TRUONG', ascending=False).head(15),
                x='MA_CN',
                y='TY_LE_TANG_TRUONG',
                title='Tỷ lệ tăng trưởng (%)',
                color='TY_LE_TANG_TRUONG',
                color_continuous_scale='RdYlGn'
            )
            st.plotly_chart(fig_growth, use_container_width=True)


def tab_customer_type_summary(data: Dict) -> None:
    """Display customer type summary."""
    st.header('👥 Tóm tắt theo Phân khúc KH')
    
    summary_cust_type = data.get('summary_customer_type', pd.DataFrame())
    if summary_cust_type.empty:
        st.info('Chưa có dữ liệu tóm tắt phân khúc khách hàng.')
        return
    
    display_cols = ['CUST_TYPE_NAME', 'SO_KH', 'TONG_T1', 'TONG_T2', 'TONG_DELTA']
    display_cols = [col for col in display_cols if col in summary_cust_type.columns]
    
    st.dataframe(summary_cust_type[display_cols].sort_values('TONG_DELTA', ascending=False), use_container_width=True)


def tab_segment_analysis(data: Dict) -> None:
    """Display segment analysis."""
    st.header('📊 Phân tích theo Segment')
    
    segment_summary = data.get('segment_summary', pd.DataFrame())
    if segment_summary.empty:
        st.info('Chưa có dữ liệu phân tích segment.')
        return
    
    display_cols = ['BALANCE_BUCKET', 'SO_KH', 'TONG_T1', 'TONG_T2', 'TONG_DELTA', 'TY_LE_TANG_TRUONG']
    display_cols = [col for col in display_cols if col in segment_summary.columns]
    
    st.dataframe(segment_summary[display_cols], use_container_width=True)


def tab_product_summary(data: Dict) -> None:
    """Display product summary."""
    st.header('💳 Tóm tắt theo Sản phẩm')
    
    summary_product = data.get('summary_product', pd.DataFrame())
    if summary_product.empty:
        st.info('Chưa có dữ liệu tóm tắt sản phẩm.')
        return
    
    display_cols = ['DP_TYPE_CODE', 'SO_KH', 'TONG_T1', 'TONG_T2', 'TONG_DELTA']
    display_cols = [col for col in display_cols if col in summary_product.columns]
    
    st.dataframe(summary_product[display_cols].sort_values('TONG_DELTA', ascending=False), use_container_width=True)


def tab_top_customers(data: Dict) -> None:
    """Display top customers analysis."""
    st.header('⭐ Top Khách hàng')
    
    comparison_df = data.get('comparison', pd.DataFrame())
    if comparison_df.empty:
        st.info('Chưa có dữ liệu khách hàng.')
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader('Top 10 khách hàng có số dư cao nhất')
        if 'TOTAL_T2' in comparison_df.columns:
            top_balance = comparison_df.nlargest(10, 'TOTAL_T2')
            display_cols = ['MA_KH', 'TEN_KH', 'MA_CN', 'TOTAL_T2', 'DELTA']
            display_cols = [col for col in display_cols if col in top_balance.columns]
            st.table(top_balance[display_cols])
    
    with col2:
        st.subheader('Top 10 khách hàng tăng trưởng mạnh nhất')
        if 'DELTA' in comparison_df.columns:
            top_growth = comparison_df.nlargest(10, 'DELTA')
            display_cols = ['MA_KH', 'TEN_KH', 'MA_CN', 'DELTA', 'TOTAL_T2']
            display_cols = [col for col in display_cols if col in top_growth.columns]
            st.table(top_growth[display_cols])


def tab_predictive_analytics(data):
    """Display predictive analytics section."""
    st.header('🔮 Dự Báo & Phân Tích Tiên Đoán')

    prediction = data.get('prediction', pd.DataFrame())
    if prediction.empty:
        placeholder = st.container(key='info_no_forecast')
        placeholder.info('Chưa có dữ liệu dự báo để hiển thị. Vui lòng chạy so sánh trước.')
        return

    prediction = normalize_forecast_columns(prediction)

    st.markdown(
        'Dự báo này sử dụng mô hình momentum đơn giản trên T1 và T2 để ước lượng kỳ tiếp theo. ' \
        'Hiển thị luôn kịch bản cơ sở, lạc quan và thận trọng để ưu tiên hành động.'
    )

    cards = [
        {'title': 'Chi nhánh nguy cơ giảm', 'value': len(prediction[prediction['FORECAST_DIRECTION'] == 'GIẢM']) if 'FORECAST_DIRECTION' in prediction.columns else 0},
        {'title': 'Chi nhánh cơ hội tăng', 'value': len(prediction[prediction['FORECAST_DIRECTION'] == 'TĂNG']) if 'FORECAST_DIRECTION' in prediction.columns else 0},
        {'title': 'Độ tin cậy cao', 'value': len(prediction[prediction['CONFIDENCE'] == 'Cao']) if 'CONFIDENCE' in prediction.columns else 0},
    ]
    cols = st.columns(len(cards))
    for col, card in zip(cols, cards):
        col.metric(card['title'], card['value'])

    st.subheader('Dự báo chi nhánh theo kịch bản')
    display_df = prediction.copy()
    display_df = display_df[['MA_CN', 'TONG_T1', 'TONG_T2', 'PREDICT_T3_BASE', 'BASE_DELTA', 'PREDICT_T3_OPT', 'OPT_DELTA', 'PREDICT_T3_PESS', 'PESS_DELTA', 'CONFIDENCE', 'FORECAST_DIRECTION', 'RISK_NOTE']]
    display_df = display_df.rename(columns={
        'PREDICT_T3_BASE': 'DỰ_BÁO_T3_CS',
        'BASE_DELTA': 'Δ_CS',
        'PREDICT_T3_OPT': 'DỰ_BÁO_T3_TỐT',
        'OPT_DELTA': 'Δ_Tốt',
        'PREDICT_T3_PESS': 'DỰ_BÁO_T3_XẤU',
        'PESS_DELTA': 'Δ_Xấu',
    })
    st.dataframe(display_df, use_container_width=True, height=380)

    if not prediction.empty:
        st.subheader('Top 5 chi nhánh cần chú ý')
        risk_branches = prediction.sort_values('BASE_DELTA').head(5).copy()
        opp_branches = prediction.sort_values('BASE_DELTA', ascending=False).head(5).copy()

        risk_branches = risk_branches.rename(columns={
            'PREDICT_T3_BASE': 'DỰ_BÁO_T3_CS',
            'BASE_DELTA': 'Δ_CS',
        })
        opp_branches = opp_branches.rename(columns={
            'PREDICT_T3_BASE': 'DỰ_BÁO_T3_CS',
            'BASE_DELTA': 'Δ_CS',
        })

        with st.expander('Chi nhánh giảm mạnh nhất'):
            st.table(risk_branches[['MA_CN', 'TONG_T2', 'DỰ_BÁO_T3_CS', 'Δ_CS', 'CONFIDENCE']])
        with st.expander('Chi nhánh tăng tốt nhất'):
            st.table(opp_branches[['MA_CN', 'TONG_T2', 'DỰ_BÁO_T3_CS', 'Δ_CS', 'CONFIDENCE']])

    st.subheader('Biểu đồ xu hướng T1 → T2 → T3')
    forecast_chart = prediction[['MA_CN', 'TONG_T1', 'TONG_T2', 'PREDICT_T3_BASE']].copy()
    top_chart = forecast_chart.sort_values('PREDICT_T3_BASE', ascending=False).head(5)
    if not top_chart.empty:
        chart_long = top_chart.melt(id_vars=['MA_CN'], value_vars=['TONG_T1', 'TONG_T2', 'PREDICT_T3_BASE'], var_name='Giai đoạn', value_name='Giá trị')
        fig = px.line(chart_long, x='Giai đoạn', y='Giá trị', color='MA_CN', markers=True,
                      title='Xu hướng chi nhánh hàng đầu theo dự báo')
        st.plotly_chart(fig, use_container_width=True)

    st.success('Dự báo này chỉ mang tính tham khảo. Nên dùng làm căn cứ để phân tích thêm và thảo luận chiến lược.')


def tab_ai_insights(data):
    """Display AI-style insights."""
    st.header('💡 AI-Powered Insights')

    insights = data.get('ai_insights', [])
    if not insights:
        placeholder = st.container(key='info_no_ai_insights')
        placeholder.info('Chưa có insights AI vì dữ liệu chưa đủ.')
        return

    strategy_cards = extract_action_insight_cards(data)
    if strategy_cards:
        st.subheader('Tóm tắt nhanh')
        cols = st.columns(len(strategy_cards))
        for col, card in zip(cols, strategy_cards):
            if card['type'] == 'action':
                col.warning(f"**{card['title']}**\n{card['message']}")
            else:
                col.info(f"**{card['title']}**\n{card['message']}")

    st.subheader('Những điểm đáng chú ý')
    for idx, insight in enumerate(insights, start=1):
        st.markdown(f"**{idx}.** {insight}")

    if data.get('prediction', pd.DataFrame()).empty and data.get('alert_summary', pd.DataFrame()).empty:
        placeholder = st.container(key='info_insights_more')
        placeholder.info('Nếu muốn insights sâu hơn, hãy chạy dữ liệu với ít nhất một lần so sánh thành công.')


def tab_alerts(data: Dict) -> None:
    """Display alerts and warnings."""
    st.header('🚨 Cảnh Báo')
    
    alert_summary = data.get('alert_summary', pd.DataFrame())
    if alert_summary.empty:
        st.info('Không có cảnh báo nào.')
        return
    
    # Alert summary metrics
    total_alerts = len(alert_summary)
    high_priority = len(alert_summary[alert_summary['MUC_UU_TIEN'] == 'CAO']) if 'MUC_UU_TIEN' in alert_summary.columns else 0
    
    col1, col2 = st.columns(2)
    col1.metric('Tổng cảnh báo', total_alerts)
    col2.metric('Ưu tiên cao', high_priority)
    
    # Display alerts
    if not alert_summary.empty and 'MUC_UU_TIEN' in alert_summary.columns:
        display_cols = ['MA_KH', 'TEN_KH', 'MA_CN', 'CANH_BAO', 'MUC_UU_TIEN', 'LY_DO']
        display_cols = [col for col in display_cols if col in alert_summary.columns]
        
        st.subheader('Danh sách cảnh báo')
        st.dataframe(alert_summary[display_cols].sort_values('MUC_UU_TIEN', ascending=False), use_container_width=True)
    elif not alert_summary.empty:
        st.info('Chưa có dữ liệu cảnh báo.')


def tab_outliers(data: Dict) -> None:
    """Display outlier analysis."""
    st.header('📈 Phân Tích Outliers')
    
    outliers = data.get('outliers', pd.DataFrame())
    if outliers.empty:
        st.info('Không có outliers được phát hiện.')
        return
    
    st.metric('Số outliers', len(outliers))
    
    display_cols = ['MA_KH', 'TEN_KH', 'MA_CN', 'TOTAL_T1', 'TOTAL_T2', 'DELTA', 'BIEN_DONG', 'OUTLIER_TYPE']
    display_cols = [col for col in display_cols if col in outliers.columns]
    
    st.dataframe(outliers[display_cols], use_container_width=True)


def tab_action_recommendations(data: Dict) -> None:
    """Display action recommendations."""
    st.header('🎯 Khuyến Nghị Hành Động')
    
    recommendations = data.get('recommendations', pd.DataFrame())
    if recommendations.empty:
        st.info('Không có khuyến nghị nào.')
        return
    
    # Recommendation summary
    if 'MUC_UU_TIEN' in recommendations.columns:
        priority_counts = recommendations['MUC_UU_TIEN'].value_counts()
        
        st.subheader('Tóm tắt khuyến nghị')
        cols = st.columns(len(priority_counts))
        for col, (priority, count) in zip(cols, priority_counts.items()):
            col.metric(f'Ưu tiên {priority}', count)
        
        # Display recommendations
        display_cols = ['MA_CN', 'KHuyen_nghi', 'MUC_UU_TIEN', 'LY_DO', 'Hanh_dong_de_xuat']
        display_cols = [col for col in display_cols if col in recommendations.columns]
        
        st.subheader('Chi tiết khuyến nghị')
        st.dataframe(recommendations[display_cols].sort_values('MUC_UU_TIEN', ascending=False), use_container_width=True)
    else:
        st.info('Chưa có cột ưu tiên trong dữ liệu khuyến nghị.')


def tab_driver_analysis(data: Dict) -> None:
    """Display driver analysis."""
    st.header('🔍 Phân Tích Nguyên Nhân')
    
    driver_analysis = data.get('driver_analysis', {})
    if not driver_analysis:
        st.info('Chưa có phân tích nguyên nhân.')
        return
    
    # Display key drivers
    if 'customer_drivers' in driver_analysis:
        st.subheader('Nguyên nhân từ khách hàng')
        for driver in driver_analysis['customer_drivers']:
            st.write(f"• {driver}")
    
    if 'product_drivers' in driver_analysis:
        st.subheader('Nguyên nhân từ sản phẩm')
        for driver in driver_analysis['product_drivers']:
            st.write(f"• {driver}")
    
    if 'market_drivers' in driver_analysis:
        st.subheader('Nguyên nhân từ thị trường')
        for driver in driver_analysis['market_drivers']:
            st.write(f"• {driver}")


def tab_custom_report_builder(data):
    """Allow user to build a custom report with selected sections."""
    st.header('🛠️ Tạo Báo Cáo Tùy Chỉnh')

    sections = [
        'Dashboard',
        'Executive summary',
        'Customer details',
        'Branch summary',
        'Customer type',
        'Product summary',
        'Segment analysis',
        'Market context',
        'Capital strategy',
        'Alerts',
        'Recommendations',
        'Predictive',
        'AI Insights',
        'Charts'
    ]
    selected_sections = st.multiselect(
        'Chọn các phần muốn bao gồm trong báo cáo:',
        sections,
        default=['Dashboard', 'Executive summary', 'Customer details', 'Branch summary', 'Alerts']
    )

    if not selected_sections:
        st.warning('Vui lòng chọn ít nhất một phần báo cáo.');
        return

    st.markdown('Bạn có thể tải báo cáo Excel chỉ chứa các bảng/section đã chọn.')
    if st.button('📥 Xuất Báo Cáo Tùy Chỉnh', use_container_width=True):
        try:
            excel_data = export_custom_report_to_excel(data, selected_sections)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'BaoCao_TuyChinh_{timestamp}.xlsx'
            st.download_button(
                label='💾 Tải xuống báo cáo tùy chỉnh',
                data=excel_data,
                file_name=filename,
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                use_container_width=True
            )
        except Exception as e:
            st.error(f'❌ Lỗi tạo báo cáo tùy chỉnh: {e}')

    st.divider()
    st.subheader('Preview nội dung đã chọn')
    for section in selected_sections:
        st.markdown(f'- {section}')


def complete_warehouse_processed_data(comparison_data: Dict) -> Dict:
    """Build the dashboard analysis payload from warehouse comparison output."""
    comparison_df = comparison_data.get('comparison', pd.DataFrame())
    all_raw_data = comparison_data.get('all_raw_data', {})

    if not comparison_df.empty:
        comparison_df = comparison_df.copy()
        comparison_df['CHURN_SCORE'] = comparison_df.apply(calculate_risk_score, axis=1)

    summary_branch_data = summary_by_branch(comparison_df)
    summary_cust_type = summary_by_customer_type(comparison_df)
    summary_product = summary_by_product_group(all_raw_data)
    summary_change = summary_by_change_type(comparison_df)

    recommendations_df, recommendation_thresholds = build_action_recommendations(comparison_df)
    driver_customer = build_driver_table(summary_cust_type, 'CUST_TYPE_NAME', 'PHAN_KHUC')
    driver_product = build_driver_table(summary_product, 'DP_GROUP', 'SAN_PHAM')
    driver_analysis = pd.concat([driver_customer, driver_product], ignore_index=True)

    segment_summary = build_segment_summary(comparison_df)
    outliers = detect_outliers_iqr(comparison_df, column='DELTA')
    alert_summary = build_alert_summary(summary_branch_data, summary_change, outliers, segment_summary, recommendations_df)
    trend_summary = build_change_type_trends(comparison_df)
    top_customers = build_top_customers(comparison_df, limit=20)
    prediction = build_predictive_forecast(summary_branch_data)

    base_payload = {
        'comparison': comparison_df,
        'summary_branch': summary_branch_data,
        'summary_product': summary_product,
        'segment_summary': segment_summary,
    }
    market_context = build_market_context({**base_payload, 'customer_data': all_raw_data})
    capital_strategy = build_capital_strategy(base_payload)
    ai_insights = build_ai_insights({
        'comparison': comparison_df,
        'summary_branch': summary_branch_data,
        'alert_summary': alert_summary,
        'top_customers': top_customers,
        'prediction': prediction,
    })

    return {
        'comparison': comparison_df,
        'summary_branch': summary_branch_data,
        'summary_cust_type': summary_cust_type,
        'summary_product': summary_product,
        'summary_change': summary_change,
        'recommendations': recommendations_df,
        'recommendation_thresholds': recommendation_thresholds,
        'driver_customer': driver_customer,
        'driver_product': driver_product,
        'driver_analysis': driver_analysis,
        'segment_summary': segment_summary,
        'alert_summary': alert_summary,
        'trend_summary': trend_summary,
        'top_customers': top_customers,
        'outliers': outliers,
        'all_raw_data': all_raw_data,
        'prediction': prediction,
        'ai_insights': ai_insights,
        'market_context': market_context,
        'capital_strategy': capital_strategy,
    }


def render_summary_metrics(data: Dict) -> None:
    """Render dashboard metric strip."""
    comparison_df = data.get('comparison', pd.DataFrame())
    branch_count = len(data.get('summary_branch', pd.DataFrame()))
    total_delta = float(comparison_df['DELTA'].sum()) if not comparison_df.empty else 0
    total_t1 = float(comparison_df['TOTAL_T1'].sum()) if not comparison_df.empty else 0
    alert_count = len(data.get('alert_summary', pd.DataFrame()))

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric('Chi nhánh', branch_count)
    col2.metric('Khách hàng', len(comparison_df))
    col3.metric('Mở mới', int((comparison_df['BIEN_DONG'] == 'MO_MOI').sum()) if not comparison_df.empty else 0)
    col4.metric('Tất toán', int((comparison_df['BIEN_DONG'] == 'TAT_TOAN').sum()) if not comparison_df.empty else 0)
    col5.metric('Tổng DELTA', f'{total_delta:,.0f}')

    col6, col7, col8 = st.columns(3)
    col6.metric('Cảnh báo', alert_count)
    col7.metric('Tăng trưởng', f'{(total_delta / max(total_t1, 1) * 100):.2f}%')
    col8.metric('Số dư T2', f"{float(comparison_df['TOTAL_T2'].sum()) if not comparison_df.empty else 0:,.0f}")


def render_compare_workspace():
    """Render comparison workflow in the main content area."""
    st.header('So sánh dữ liệu')
    st.caption('Chọn ngày dữ liệu T1/T2 từ kho. Có thể chọn 1 hoặc nhiều file để so sánh cùng lúc.')

    warehouse_files = list_warehouse_files()
    if warehouse_files.empty:
        st.warning('Kho dữ liệu đang trống. Hãy import file trong màn Kho dữ liệu trước.')
        return

    warehouse_files['data_date'] = pd.to_datetime(warehouse_files['data_date'], errors='coerce')
    warehouse_files['import_date'] = pd.to_datetime(warehouse_files['import_date'], errors='coerce')
    dated_files = warehouse_files.dropna(subset=['data_date']).copy()
    dated_files = filter_files_by_branch_access(dated_files)
    if dated_files.empty:
        st.warning('Chưa có file hợp lệ trong phạm vi chi nhánh được cấp quyền.')
        return

    dated_files['date_only'] = dated_files['data_date'].dt.date
    available_dates = sorted(dated_files['date_only'].unique(), reverse=True)

    col_t1, col_t2 = st.columns(2)
    with col_t1:
        t1_date = st.selectbox(
            'T1 - ngày dữ liệu cũ',
            options=available_dates,
            index=1 if len(available_dates) > 1 else 0,
            format_func=lambda d: d.strftime('%d/%m/%Y'),
            key='dashboard_t1_data_date',
        )
    with col_t2:
        t2_date = st.selectbox(
            'T2 - ngày dữ liệu mới',
            options=available_dates,
            index=0,
            format_func=lambda d: d.strftime('%d/%m/%Y'),
            key='dashboard_t2_data_date',
        )

    def latest_per_branch(df: pd.DataFrame) -> pd.DataFrame:
        return (
            df.sort_values('import_date', ascending=False)
            .drop_duplicates(subset=['branch_code'], keep='first')
            .sort_values('branch_code')
        )

    t1_files = dated_files[dated_files['date_only'] == t1_date].sort_values(['branch_code', 'import_date'], ascending=[True, False])
    t2_files = dated_files[dated_files['date_only'] == t2_date].sort_values(['branch_code', 'import_date'], ascending=[True, False])

    st.subheader('Chọn file T1 / T2 để so sánh')
    t1_label_map = {
        row['id']: f"{row['original_name']} ({row['branch_code']} - {row['record_count']} rec)"
        for _, row in t1_files.iterrows()
    }
    t2_label_map = {
        row['id']: f"{row['original_name']} ({row['branch_code']} - {row['record_count']} rec)"
        for _, row in t2_files.iterrows()
    }

    t1_selected = st.multiselect(
        'Chọn file T1:',
        options=t1_files['id'].tolist(),
        default=t1_files['id'].tolist(),
        format_func=lambda x: t1_label_map.get(x, str(x)),
        key='dashboard_t1_file_selection'
    )

    if t1_selected:
        suggestions = suggest_file_pairs(t1_selected, t2_files)
        if suggestions:
            st.caption('💡 Gợi ý T2 cho các file T1 đã chọn.')
            if st.button('💡 Áp dụng gợi ý T2', key='dashboard_apply_t2_suggestions'):
                st.session_state.dashboard_t2_file_selection = list(suggestions.values())

    t2_selected = st.multiselect(
        'Chọn file T2:',
        options=t2_files['id'].tolist(),
        default=t2_files['id'].tolist(),
        format_func=lambda x: t2_label_map.get(x, str(x)),
        key='dashboard_t2_file_selection'
    )

    t1_selected_files = t1_files[t1_files['id'].isin(t1_selected)]
    t2_selected_files = t2_files[t2_files['id'].isin(t2_selected)]

    st.subheader('Kiểm tra chi nhánh')
    t1_branch_set = set(t1_selected_files['branch_code'].dropna())
    t2_branch_set = set(t2_selected_files['branch_code'].dropna())
    all_branches = sorted(t1_branch_set | t2_branch_set)
    branch_check = pd.DataFrame([
        {
            'MA_CN': branch,
            'T1': 'Có' if branch in t1_branch_set else 'Thiếu',
            'T2': 'Có' if branch in t2_branch_set else 'Thiếu',
            'Trạng thái': 'OK' if branch in t1_branch_set and branch in t2_branch_set else 'Lệch',
        }
        for branch in all_branches
    ])
    st.dataframe(branch_check, use_container_width=True, hide_index=True)

    valid_pair = bool(t1_selected and t2_selected and t1_date != t2_date)
    status_label = 'Hợp lệ' if valid_pair else 'Chưa hợp lệ'
    if t1_selected and t2_selected and t1_date == t2_date:
        status_label = 'T1 và T2 không thể cùng ngày'

    col_status, col_run = st.columns([0.7, 0.3])
    with col_status:
        st.write(
            f"T1: {len(t1_selected)} file | T2: {len(t2_selected)} file | Trạng thái: {status_label}"
        )
    with col_run:
        compare_clicked = st.button('So sánh dữ liệu', disabled=not valid_pair, type='primary', use_container_width=True)

    if compare_clicked:
        try:
            progress = st.progress(0)
            status = st.empty()
            status.text('Đang lấy dữ liệu từ kho...')
            progress.progress(15)

            comparison_data = build_comparison_from_warehouse(t1_selected, t2_selected, None)
            cache_key = f"warehouse_{'_'.join(map(str, sorted(t1_selected)))}_vs_{'_'.join(map(str, sorted(t2_selected))) }"
            cache_key_hash = hashlib.sha256(cache_key.encode()).hexdigest()

            status.text('Đang xử lý đối chiếu...')
            progress.progress(45)
            cached = load_processed_data(cache_key_hash)
            if cached and 'comparison' in cached:
                processed = cached
                cache_hit = 'YES'
            else:
                processed = complete_warehouse_processed_data(comparison_data)
                cache_hit = 'NO'

            status.text('Đang lưu kết quả...')
            progress.progress(85)
            st.session_state.processed_data = processed
            if cache_hit == 'NO':
                save_processed_data(cache_key_hash, processed)

            comparison_df = processed['comparison']
            append_history({
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'cache_key': cache_key_hash,
                't1_input_files': ';'.join(t1_selected_files['original_name'].tolist()),
                't2_input_files': ';'.join(t2_selected_files['original_name'].tolist()),
                't1_files': len(t1_selected),
                't2_files': len(t2_selected),
                't1_date': t1_date.strftime('%Y-%m-%d'),
                't2_date': t2_date.strftime('%Y-%m-%d'),
                'branches': len(processed['summary_branch']),
                'customers': len(comparison_df),
                'total_t1': round(float(comparison_df['TOTAL_T1'].sum()), 2) if not comparison_df.empty else 0,
                'total_t2': round(float(comparison_df['TOTAL_T2'].sum()), 2) if not comparison_df.empty else 0,
                'total_delta': round(float(comparison_df['DELTA'].sum()), 2) if not comparison_df.empty else 0,
                'high_risk_customers': len(processed['recommendations'][processed['recommendations']['MUC_UU_TIEN'] == 'RAT_CAO']) if not processed['recommendations'].empty and 'MUC_UU_TIEN' in processed['recommendations'].columns else 0,
                'cache_hit': cache_hit,
            })
            log_audit(
                'SYSTEM', 'RUN_COMPARISON', 'comparison', None, None,
                f"Compared {t1_date.strftime('%Y-%m-%d')} vs {t2_date.strftime('%Y-%m-%d')} with {len(t1_selected)} branches"
            )
            progress.progress(100)
            status.text('Hoàn tất')
            st.success('So sánh thành công. Chuyển sang Dashboard hoặc Phân tích để xem kết quả.')
        except Exception as e:
            st.error(f'Lỗi xử lý so sánh: {e}')


def render_warehouse_workspace():
    """Render warehouse management in main area."""
    st.header('Kho dữ liệu')
    tab_import, tab_dates, tab_files, tab_stats = st.tabs(['Import', 'Dữ liệu theo ngày', 'Danh sách file', 'Thống kê'])
    with tab_import:
        render_import_section()
    with tab_dates:
        render_calendar_view()
    with tab_files:
        render_enhanced_file_list()
    with tab_stats:
        render_statistics_section()


def render_analysis_workspace(data: Optional[Dict]):
    """Render analysis screens."""
    st.header('Phân tích')
    if not data:
        placeholder = st.container(key='info_no_analysis_data')
        placeholder.info('Chưa có dữ liệu phân tích. Hãy chạy so sánh trước.')
        return

    section = st.selectbox('Nhóm phân tích', ['Chi tiết', 'Dự báo', 'Insights AI', 'Cảnh báo', 'Khuyến nghị'])
    if section == 'Chi tiết':
        tab_customer_details(data)
        st.divider()
        tab_branch_summary(data)
        st.divider()
        tab_customer_type_summary(data)
        st.divider()
        tab_segment_analysis(data)
        st.divider()
        tab_product_summary(data)
        st.divider()
        tab_top_customers(data)
    elif section == 'Dự báo':
        tab_predictive_analytics(data)
    elif section == 'Insights AI':
        tab_ai_insights(data)
    elif section == 'Cảnh báo':
        tab_alerts(data)
        st.divider()
        tab_outliers(data)
    elif section == 'Khuyến nghị':
        tab_action_recommendations(data)
        st.divider()
        tab_driver_analysis(data)


def render_report_workspace(data: Optional[Dict]):
    """Render report/export screens."""
    st.header('Báo cáo')
    if not data:
        placeholder = st.container(key='info_no_report_data')
        placeholder.info('Chưa có dữ liệu báo cáo. Hãy chạy so sánh trước.')
        return

    section = st.selectbox('Loại báo cáo', ['Biểu đồ & Excel', 'Báo cáo tùy chỉnh', 'Chia sẻ'])
    if section == 'Biểu đồ & Excel':
        tab_charts(data)
        st.divider()
        tab_export(data)
    elif section == 'Báo cáo tùy chỉnh':
        tab_custom_report_builder(data)
    elif section == 'Chia sẻ':
        render_sharing_interface(data)


def tab_charts(data: Dict) -> None:
    """Display comprehensive charts for reporting."""
    st.header('📊 Biểu đồ Báo cáo')
    
    comparison_df = data.get('comparison', pd.DataFrame())
    summary_branch = data.get('summary_branch', pd.DataFrame())
    
    if comparison_df.empty:
        st.info('Chưa có dữ liệu để tạo biểu đồ.')
        return
    
    # Overview charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Customer change distribution
        if 'BIEN_DONG' in comparison_df.columns:
            change_counts = comparison_df['BIEN_DONG'].value_counts()
            fig_change = px.pie(
                values=change_counts.values,
                names=change_counts.index,
                title='Phân bố biến động khách hàng'
            )
            st.plotly_chart(fig_change, use_container_width=True)
    
    with col2:
        # Balance distribution
        if 'TOTAL_T2' in comparison_df.columns:
            fig_balance = px.histogram(
                comparison_df,
                x='TOTAL_T2',
                nbins=30,
                title='Phân bố số dư T2',
                marginal='box'
            )
            st.plotly_chart(fig_balance, use_container_width=True)
    
    st.divider()
    
    # Branch analysis charts
    if not summary_branch.empty:
        col3, col4 = st.columns(2)
        
        with col3:
            if 'TONG_DELTA' in summary_branch.columns:
                fig_branch_delta = px.bar(
                    summary_branch.sort_values('TONG_DELTA', ascending=False).head(15),
                    x='MA_CN',
                    y='TONG_DELTA',
                    title='DELTA theo chi nhánh (Top 15)',
                    color='TONG_DELTA',
                    color_continuous_scale='RdYlGn'
                )
                st.plotly_chart(fig_branch_delta, use_container_width=True)
        
        with col4:
            if 'TY_LE_TANG_TRUONG' in summary_branch.columns:
                fig_growth = px.bar(
                    summary_branch.sort_values('TY_LE_TANG_TRUONG', ascending=False).head(15),
                    x='MA_CN',
                    y='TY_LE_TANG_TRUONG',
                    title='Tỷ lệ tăng trưởng (%)',
                    color='TY_LE_TANG_TRUONG',
                    color_continuous_scale='RdYlGn'
                )
                st.plotly_chart(fig_growth, use_container_width=True)
    
    # Customer segment analysis
    if 'CUST_TYPE_NAME' in comparison_df.columns:
        st.subheader('Phân tích theo phân khúc khách hàng')
        cust_type_summary = comparison_df.groupby('CUST_TYPE_NAME').agg({
            'DELTA': 'sum',
            'TOTAL_T2': 'sum',
            'MA_KH': 'count'
        }).reset_index()
        
        fig_cust_type = px.bar(
            cust_type_summary.sort_values('DELTA', ascending=False),
            x='CUST_TYPE_NAME',
            y='DELTA',
            title='DELTA theo phân khúc khách hàng',
            color='DELTA',
            color_continuous_scale='RdYlGn'
        )
        st.plotly_chart(fig_cust_type, use_container_width=True)


def tab_export(data: Dict) -> None:
    """Export comprehensive Excel report."""
    st.header('📊 Xuất Báo Cáo Excel')
    
    st.markdown('Xuất báo cáo Excel đầy đủ với tất cả dữ liệu phân tích.')
    
    if st.button('📥 Xuất Báo Cáo Đầy Đủ', use_container_width=True, type='primary'):
        try:
            from exporter import export_to_excel
            
            # Prepare comprehensive export data
            export_data = {}
            
            # Add all available data sections
            if data.get('comparison') is not None and not data['comparison'].empty:
                export_data['So sánh khách hàng'] = data['comparison'].copy()
            
            if data.get('summary_branch') is not None and not data['summary_branch'].empty:
                export_data['Tóm tắt chi nhánh'] = data['summary_branch'].copy()
            
            if data.get('summary_customer_type') is not None and not data['summary_customer_type'].empty:
                export_data['Tóm tắt phân khúc KH'] = data['summary_customer_type'].copy()
            
            if data.get('summary_product') is not None and not data['summary_product'].empty:
                export_data['Tóm tắt sản phẩm'] = data['summary_product'].copy()
            
            if data.get('segment_summary') is not None and not data['segment_summary'].empty:
                export_data['Phân tích segment'] = data['segment_summary'].copy()
            
            if data.get('recommendations') is not None and not data['recommendations'].empty:
                export_data['Khuyến nghị'] = data['recommendations'].copy()
            
            if data.get('alert_summary') is not None and not data['alert_summary'].empty:
                export_data['Cảnh báo'] = data['alert_summary'].copy()
            
            if data.get('prediction') is not None and not data['prediction'].empty:
                export_data['Dự báo'] = data['prediction'].copy()
            
            if data.get('outliers') is not None and not data['outliers'].empty:
                export_data['Outliers'] = data['outliers'].copy()
            
            if not export_data:
                st.warning('Không có dữ liệu để xuất.')
                return
            
            # Create Excel export directly
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                for sheet_name, df in export_data.items():
                    if not df.empty:
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            excel_data = output.getvalue()
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'BaoCao_DayDu_{timestamp}.xlsx'
            
            st.download_button(
                label='💾 Tải xuống báo cáo đầy đủ',
                data=excel_data,
                file_name=filename,
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                use_container_width=True
            )
            
            st.success(f'✅ Báo cáo Excel đã sẵn sàng tải xuống: {filename}')
            
        except Exception as e:
            st.error(f'❌ Lỗi xuất báo cáo: {e}')


def render_settings_workspace():
    """Render app settings and history in main area."""
    st.header('Cài đặt')
    st.divider()

    st.subheader('Lịch sử so sánh')
    history_df = load_history()
    if history_df.empty:
        st.caption('Chưa có lịch sử xử lý.')
        return

    history_df_display = history_df.copy()
    if 'cache_key' in history_df_display.columns:
        history_df_display = history_df_display.drop(columns=['cache_key'])

    st.dataframe(history_df_display, use_container_width=True, hide_index=True)

    history_labels = []
    for _, row in history_df.iterrows():
        total_delta = float(row['total_delta']) if pd.notna(row['total_delta']) else 0
        label = (
            f"{row['timestamp']} | T1={row['t1_date']} ({row['t1_files']} file)"
            f" - T2={row['t2_date']} ({row['t2_files']} file) | KH={row['customers']} | Δ={total_delta:,.0f}"
        )
        history_labels.append((label, row['cache_key']))

    selected_cache_key = st.selectbox(
        'Chọn lần so sánh để xem lại',
        [label for label, _ in history_labels],
        key='selected_history_entry'
    )

    if selected_cache_key:
        selected_index = [label for label, _ in history_labels].index(selected_cache_key)
        selected_key = history_labels[selected_index][1]

        col1, col2 = st.columns([2, 1])
        with col1:
            if st.button('Xem lại phân tích', key='review_history'):
                loaded_data = load_processed_data(selected_key)
                if loaded_data and isinstance(loaded_data, dict):
                    st.session_state['history_loaded_data'] = loaded_data
                    st.success('Đã tải lại phân tích từ lịch sử. Chuyển sang trang Phân tích để xem chi tiết.')
                else:
                    st.error('Không tìm thấy dữ liệu phân tích cho lần so sánh này. Có thể cache đã bị xóa hoặc bị hỏng.')

        with col2:
            if st.button('Xem dữ liệu hiện tại', key='clear_history_view'):
                st.session_state['history_loaded_data'] = None
                st.success('Đã chuyển về dữ liệu phân tích hiện tại.')

    st.download_button(
        label='Tải lịch sử CSV',
        data=history_df.to_csv(index=False).encode('utf-8-sig'),
        file_name='comparison_history_recent.csv',
        mime='text/csv',
    )
    if st.button('Dọn dẹp cache cũ', help='Xóa cache entries cũ hơn 30 ngày'):
        cleanup_old_cache(30)


def render_sidebar_navigation() -> str:
    """Render a dashboard-style left navigation and return the active page."""
    nav_items = [
        ('Dashboard', 'Tổng quan', 'dashboard.view', 'Tổng hợp nhanh kết quả phân tích'),
        ('Kho dữ liệu', 'Kho dữ liệu', 'warehouse.view', 'Import, lịch dữ liệu và quản lý file'),
        ('So sánh dữ liệu', 'So sánh', 'comparison.run', 'Chọn T1/T2 và chạy đối chiếu'),
        ('Phân tích', 'Phân tích', 'analysis.view', 'Chi tiết, cảnh báo, AI và khuyến nghị'),
        ('Báo cáo', 'Báo cáo', 'report.view', 'Biểu đồ, Excel và chia sẻ'),
        ('Cài đặt', 'Cài đặt', 'settings.history', 'Mapping cột, lịch sử và cache'),
    ]
    visible_items = nav_items

    if 'main_dashboard_page' not in st.session_state:
        st.session_state.main_dashboard_page = visible_items[0][0] if visible_items else ''

    if visible_items and st.session_state.main_dashboard_page not in [item[0] for item in visible_items]:
        st.session_state.main_dashboard_page = visible_items[0][0]

    st.markdown(
        """
        <div class="sidebar-brand">
            <div class="sidebar-brand-title">Thi đua</div>
            <div class="sidebar-brand-subtitle">Tiền gửi & phân tích</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not visible_items:
        st.warning('Tài khoản chưa được cấp quyền chức năng nào.')
        return ''

    for page_key, label, _, help_text in visible_items:
        is_active = st.session_state.main_dashboard_page == page_key
        button_type = 'primary' if is_active else 'secondary'
        if st.button(label, key=f'nav_{page_key}', help=help_text, use_container_width=True, type=button_type):
            st.session_state.main_dashboard_page = page_key
            st.rerun()

    return st.session_state.main_dashboard_page


def main():
    """Dashboard-layout application entry point."""
    init_session_state()

    if st.query_params.get("session"):
        render_shared_analysis_viewer()
        return

    with st.sidebar:
        selected_page = render_sidebar_navigation()
        st.markdown('---')
        data_ready = st.session_state.processed_data is not None
        st.caption(f"Trạng thái: {'Đã có dữ liệu phân tích' if data_ready else 'Chưa chạy so sánh'}")

    st.markdown('<div class="main-header">Hệ Thống So Sánh Dữ Liệu Tiền Gửi</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Dashboard nghiệp vụ theo kho dữ liệu, kỳ so sánh và báo cáo phân tích</div>', unsafe_allow_html=True)

    data = get_active_analysis_data()

    if selected_page == 'Dashboard':
        if data:
            render_summary_metrics(data)
            st.divider()
            tab_dashboard(data)
        else:
            placeholder = st.container(key='info_no_analysis_sidebar')
            placeholder.info('Chưa có dữ liệu phân tích. Vào Kho dữ liệu để import file, sau đó vào So sánh dữ liệu để chọn T1/T2.')
    elif selected_page == 'Kho dữ liệu':
        render_warehouse_workspace()
    elif selected_page == 'So sánh dữ liệu':
        render_compare_workspace()
    elif selected_page == 'Phân tích':
        render_analysis_workspace(data)
    elif selected_page == 'Báo cáo':
        render_report_workspace(data)
    elif selected_page == 'Cài đặt':
        render_settings_workspace()


if __name__ == "__main__":
    main()
