"""
Main Streamlit application for deposit comparison system.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import os
import io
from datetime import datetime
import tempfile

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
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'processed_data' not in st.session_state:
    st.session_state.processed_data = None
if 'validation_result' not in st.session_state:
    st.session_state.validation_result = None


def main():
    """Main application function."""
    
    # Header
    st.markdown('<div class="main-header">📊 Hệ Thống So Sánh Dữ Liệu Tiền Gửi</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">So sánh dữ liệu tiền gửi giữa 2 quý (T1 và T2)</div>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("📥 Quy Trình Xử Lý")
        
        # Show guide
        with st.expander("📖 Hướng Dẫn Sử Dụng", expanded=True):
            st.markdown("""
            ### 🎯 Các Bước Thực Hiện:
            
            **Bước 1️⃣: Chuẩn Bị Dữ Liệu**
            - Tải dữ liệu T1 (quý trước)
            - Tải dữ liệu T2 (quý đối chiếu)
            - Format: `{MA_CN}_dp01_yyyymmdd.csv`
            
            **Bước 2️⃣: Khởi Động Xử Lý**
            - Bấm nút "🔄 Xử Lý Đối Chiếu"
            - Hệ thống sẽ kiểm tra và xử lý dữ liệu
            
            **Bước 3️⃣: Xem Kết Quả**
            - Chọn tab để xem các báo cáo khác nhau
            - So sánh, phân tích, xuất Excel
            """)
        
        st.divider()
        st.subheader("📋 Tải Tệp Dữ Liệu")
        
        st.write("**T1 - Dữ Liệu Quý Trước:**")
        t1_files = st.file_uploader(
            "Chọn file T1",
            type="csv",
            accept_multiple_files=True,
            key="t1_files",
            help="Chọn một hoặc nhiều file CSV của quý trước"
        )
        
        st.write("**T2 - Dữ Liệu Quý Đối Chiếu:**")
        t2_files = st.file_uploader(
            "Chọn file T2",
            type="csv",
            accept_multiple_files=True,
            key="t2_files",
            help="Chọn một hoặc nhiều file CSV của quý đối chiếu"
        )
        
        st.divider()
        
        # Process button with enhanced styling
        col1, col2 = st.columns([2, 1])
        with col1:
            process_clicked = st.button("🔄 Xử Lý Đối Chiếu", use_container_width=True, type="primary")
        
        if process_clicked:
            if not t1_files or not t2_files:
                st.error("❌ Vui lòng tải lên file cho cả T1 và T2")
            else:
                try:
                    # Create progress tracking
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    # Step 1: Save files
                    status_text.text("📁 Đang lưu tệp...")
                    progress_bar.progress(20)
                    
                    temp_dir = tempfile.mkdtemp()
                    t1_paths = []
                    t2_paths = []
                    
                    for file in t1_files:
                        path = os.path.join(temp_dir, file.name)
                        with open(path, 'wb') as f:
                            f.write(file.getbuffer())
                        t1_paths.append(path)
                    
                    for file in t2_files:
                        path = os.path.join(temp_dir, file.name)
                        with open(path, 'wb') as f:
                            f.write(file.getbuffer())
                        t2_paths.append(path)
                    
                    # Step 2: Validate files
                    status_text.text("🔍 Đang kiểm tra tệp...")
                    progress_bar.progress(40)
                    validation = validate_all_files(t1_paths, t2_paths)
                    st.session_state.validation_result = validation
                    
                    # Step 3: Process data
                    status_text.text("⚙️ Đang xử lý dữ liệu...")
                    progress_bar.progress(60)
                    processed = process_data(t1_paths, t2_paths, validation)
                    
                    # Step 4: Prepare results
                    status_text.text("💾 Đang chuẩn bị kết quả...")
                    progress_bar.progress(80)
                    st.session_state.processed_data = processed
                    st.session_state.temp_dir = temp_dir
                    
                    # Finalize
                    progress_bar.progress(100)
                    status_text.text("✅ Hoàn tất!")
                    
                    # Clear progress after 1 second
                    import time
                    time.sleep(1)
                    progress_bar.empty()
                    status_text.empty()
                    
                    st.success(f"✅ Xử lý thành công! {len(t1_files)} file T1, {len(t2_files)} file T2")
                    st.balloons()
                    
                except ValidationError as e:
                    st.error(f"❌ Lỗi kiểm tra: {str(e)}")
                except Exception as e:
                    st.error(f"❌ Lỗi xử lý: {str(e)}")
        
        # Show tips
        with st.expander("💡 Mẹo & Thông Tin"):
            st.markdown("""
            **📌 Định Dạng File:**
            - File phải có tên: `{MA_CN}_dp01_yyyymmdd.csv`
            - Ví dụ: `2021_dp01_20231231.csv`
            
            **📊 Cột Bắt Buộc:**
            - MA_KH: Mã khách hàng
            - TEN_KH: Tên khách hàng
            - AMOUNT: Số tiền
            - DP_TYPE_CODE: Loại sản phẩm
            
            **⚡ Lưu Ý:**
            - T1 và T2 phải có cùng cấu trúc cột
            - File CSV phải là UTF-8 encoding
            - Dữ liệu sẽ xóa sau khi tắt app
            """)
    
    # Main content area
    if st.session_state.processed_data:
        data = st.session_state.processed_data
        
        # Summary cards
        st.markdown("### 📊 Tóm Tắt Nhanh")
        col1, col2, col3, col4, col5 = st.columns(5)
        
        comparison_df = data['comparison']
        with col1:
            st.metric("📈 Tổng KH", len(comparison_df))
        with col2:
            new_customers = len(comparison_df[comparison_df['BIEN_DONG'] == 'MO_MOI'])
            st.metric("🆕 Mở Mới", new_customers)
        with col3:
            closed = len(comparison_df[comparison_df['BIEN_DONG'] == 'TAT_TOAN'])
            st.metric("🔚 Tất Toán", closed)
        with col4:
            increased = len(comparison_df[comparison_df['BIEN_DONG'] == 'TANG'])
            st.metric("📈 Tăng", increased)
        with col5:
            total_delta = comparison_df['DELTA'].sum()
            st.metric("💰 Tổng Δ", f"{total_delta:,.0f}")
        
        st.divider()
        
        # Create tabs
        tabs = st.tabs([
            "📋 Chi Tiết Khách Hàng",
            "📊 Theo Chi Nhánh",
            "👥 Theo Phân Khúc",
            "📦 Theo Sản Phẩm",
            "🚨 Bất Thường",
            "📈 Biểu Đồ",
            "💾 Xuất Báo Cáo"
        ])
        
        # Tab 1: Customer Details
        with tabs[0]:
            tab_customer_details(data)
        
        # Tab 2: Branch Summary
        with tabs[1]:
            tab_branch_summary(data)
        
        # Tab 3: Customer Type Summary
        with tabs[2]:
            tab_customer_type_summary(data)
        
        # Tab 4: Product Group Summary
        with tabs[3]:
            tab_product_summary(data)
        
        # Tab 5: Outliers
        with tabs[4]:
            tab_outliers(data)
        
        # Tab 6: Charts
        with tabs[5]:
            tab_charts(data)
        
        # Tab 7: Export
        with tabs[6]:
            tab_export(data)
    else:
        # Welcome screen
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("""
            <div class="step-guide">
                <h3>👋 Chào Mừng!</h3>
                <p>Hãy bắt đầu bằng cách:</p>
                <ol>
                    <li>📂 Tải file T1 (quý trước)</li>
                    <li>📂 Tải file T2 (quý đối chiếu)</li>
                    <li>🔘 Bấm nút "Xử Lý Đối Chiếu"</li>
                </ol>
                <p style="text-align: center; margin-top: 20px;">
                    👈 Sử dụng thanh bên trái để bắt đầu
                </p>
            </div>
            """, unsafe_allow_html=True)


def process_data(t1_paths, t2_paths, validation):
    """Process uploaded data and generate statistics."""
    
    # Create file mapping
    file_mapping = {}
    branch_dates = validation['branch_dates']
    
    # Create mapping from file paths
    t1_by_name = {os.path.basename(p): p for p in t1_paths}
    t2_by_name = {os.path.basename(p): p for p in t2_paths}
    
    for ma_cn in branch_dates.keys():
        t1_date, t2_date = branch_dates[ma_cn]
        t1_filename = f"{ma_cn}_dp01_{t1_date}.csv"
        t2_filename = f"{ma_cn}_dp01_{t2_date}.csv"
        
        if t1_filename in t1_by_name and t2_filename in t2_by_name:
            file_mapping[ma_cn] = (t1_by_name[t1_filename], t2_by_name[t2_filename])
    
    # Load and process data
    all_raw_data = {}
    all_aggregated = {}
    comparison_results = []
    
    for ma_cn, (t1_file, t2_file) in file_mapping.items():
        # Load data
        df_t1 = load_and_normalize_csv(t1_file)
        df_t2 = load_and_normalize_csv(t2_file)
        
        all_raw_data[ma_cn] = {'T1': df_t1, 'T2': df_t2}
        
        # Filter invalid data
        df_t1_filtered = filter_valid_data(df_t1)
        df_t2_filtered = filter_valid_data(df_t2)
        
        # Aggregate
        agg_t1, agg_t2 = aggregate_pair(df_t1_filtered, df_t2_filtered)
        all_aggregated[ma_cn] = {'T1': agg_t1, 'T2': agg_t2}
        
        # Compare
        comparison = merge_and_compare(agg_t1, agg_t2, ma_cn)
        comparison_results.append(comparison)
    
    # Combine all comparisons
    comparison_df = pd.concat(comparison_results, ignore_index=True) if comparison_results else pd.DataFrame()
    
    # Generate summaries
    summary_branch_data = summary_by_branch(comparison_df)
    summary_cust_type = summary_by_customer_type(comparison_df)
    summary_product = summary_by_product_group(all_raw_data)
    summary_change = summary_by_change_type(comparison_df)
    
    # Detect outliers
    outliers = detect_outliers_iqr(comparison_df, column='DELTA')
    
    return {
        'comparison': comparison_df,
        'summary_branch': summary_branch_data,
        'summary_cust_type': summary_cust_type,
        'summary_product': summary_product,
        'summary_change': summary_change,
        'outliers': outliers,
        'all_raw_data': all_raw_data,
        'validation': st.session_state.validation_result
    }


def tab_customer_details(data):
    """Display detailed customer information."""
    st.header("📋 Chi Tiết Khách Hàng")
    
    comparison_df = data['comparison']
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        selected_branches = st.multiselect(
            "Chi Nhánh",
            comparison_df['MA_CN'].unique(),
            default=comparison_df['MA_CN'].unique(),
            key="branch_filter"
        )
    
    with col2:
        selected_types = st.multiselect(
            "Phân Khúc",
            comparison_df['CUST_TYPE_NAME'].unique(),
            default=comparison_df['CUST_TYPE_NAME'].unique(),
            key="type_filter"
        )
    
    with col3:
        selected_changes = st.multiselect(
            "Biến Động",
            comparison_df['BIEN_DONG'].unique(),
            default=comparison_df['BIEN_DONG'].unique(),
            key="change_filter"
        )
    
    # Apply filters
    filtered_df = comparison_df[
        (comparison_df['MA_CN'].isin(selected_branches)) &
        (comparison_df['CUST_TYPE_NAME'].isin(selected_types)) &
        (comparison_df['BIEN_DONG'].isin(selected_changes))
    ].copy()
    
    # Format for display
    display_df = filtered_df.copy()
    for col in ['TOTAL_T1', 'TOTAL_T2', 'DELTA']:
        display_df[col] = display_df[col].apply(lambda x: f"{x:,.0f}")
    
    st.dataframe(display_df, use_container_width=True, height=400)
    
    # Statistics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Tổng Khách Hàng", len(filtered_df))
    with col2:
        st.metric("Mở Mới", len(filtered_df[filtered_df['BIEN_DONG'] == 'MO_MOI']))
    with col3:
        st.metric("Tất Toán", len(filtered_df[filtered_df['BIEN_DONG'] == 'TAT_TOAN']))
    with col4:
        st.metric("Tăng", len(filtered_df[filtered_df['BIEN_DONG'] == 'TANG']))
    
    # Export filtered data to Excel
    if not filtered_df.empty:
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("📥 Xuất Excel (Dữ Liệu Đã Lọc)", use_container_width=True, key="export_filtered"):
                try:
                    # Create fast Excel export
                    export_df = filtered_df.copy()
                    # Format numeric columns
                    for col in ['TOTAL_T1', 'TOTAL_T2', 'DELTA']:
                        if col in export_df.columns:
                            export_df[col] = export_df[col].apply(lambda x: f"{x:,.0f}" if pd.notna(x) else "0")
                    
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        export_df.to_excel(writer, sheet_name='Khách Hàng Đã Lọc', index=False)
                        
                        ws = writer.sheets['Khách Hàng Đã Lọc']
                        from openpyxl.styles import Font, PatternFill
                        from openpyxl.utils import get_column_letter
                        
                        header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
                        header_font = Font(bold=True, color="FFFFFF")
                        
                        for cell in ws[1]:
                            cell.fill = header_fill
                            cell.font = header_font
                        
                        for col_num in range(1, len(export_df.columns) + 1):
                            ws.column_dimensions[get_column_letter(col_num)].width = 15
                    
                    output.seek(0)
                    excel_data = output.getvalue()
                    
                    # Generate filename with timestamp
                    from datetime import datetime
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"ChiTietKhachHang_Loc_{timestamp}.xlsx"
                    
                    st.download_button(
                        label="💾 Tải Xuống Excel",
                        data=excel_data,
                        file_name=filename,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml"
                    )
                    
                    st.success(f"✅ Đã chuẩn bị file Excel: {filename}")
                    
                except Exception as e:
                    st.error(f"❌ Lỗi xuất Excel: {str(e)}")


def tab_branch_summary(data):
    """Display summary by branch."""
    st.header("📊 Thống Kê Theo Chi Nhánh")
    
    st.info("📌 So sánh dữ liệu tiền gửi giữa T1 và T2 theo từng chi nhánh, bao gồm tỷ lệ tăng trưởng")
    
    summary_branch = data['summary_branch']
    
    # Format for display
    display_df = summary_branch.copy()
    for col in ['TONG_T1', 'TONG_T2', 'TONG_DELTA']:
        display_df[col] = display_df[col].apply(lambda x: f"{x:,.0f}")
    display_df['TY_LE_TANG_TRUONG'] = display_df['TY_LE_TANG_TRUONG'].apply(lambda x: f"{x:.2%}")
    
    st.dataframe(display_df, use_container_width=True)
    
    # Summary metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        total_t1 = summary_branch['TONG_T1'].sum()
        st.metric("Tổng T1", f"{total_t1:,.0f}")
    with col2:
        total_t2 = summary_branch['TONG_T2'].sum()
        st.metric("Tổng T2", f"{total_t2:,.0f}")
    with col3:
        total_delta = summary_branch['TONG_DELTA'].sum()
        st.metric("Tổng DELTA", f"{total_delta:,.0f}")
    
    with st.expander("ℹ️ Giải Thích"):
        st.markdown("""
        **TONG_T1:** Tổng dư tiền của chi nhánh ở quý 1
        **TONG_T2:** Tổng dư tiền của chi nhánh ở quý 2
        **TONG_DELTA:** Chênh lệch (TONG_T2 - TONG_T1)
        **TY_LE_TANG_TRUONG:** Tỷ lệ tăng (hay giảm) so với quý trước
        """)


def tab_customer_type_summary(data):
    """Display summary by customer type."""
    st.header("👥 Thống Kê Theo Phân Khúc")
    
    st.info("📌 Phân tích dữ liệu giữa khách hàng Cá Nhân và Pháp Nhân")
    
    summary_cust = data['summary_cust_type']
    
    # Format for display
    display_df = summary_cust.copy()
    for col in ['TONG_T1', 'TONG_T2', 'TONG_DELTA']:
        display_df[col] = display_df[col].apply(lambda x: f"{x:,.0f}")
    
    st.dataframe(display_df, use_container_width=True)
    
    # Chart
    if not summary_cust.empty:
        fig = px.bar(
            summary_cust,
            x='CUST_TYPE_NAME',
            y=['TONG_T1', 'TONG_T2'],
            barmode='group',
            title='So Sánh Giữa T1 và T2 Theo Phân Khúc'
        )
        st.plotly_chart(fig, use_container_width=True)


def tab_product_summary(data):
    """Display summary by product group."""
    st.header("📦 Thống Kê Theo Nhóm Sản Phẩm")
    
    st.info("📌 Phân tích dữ liệu tiền gửi theo từng loại sản phẩm")
    
    summary_product = data['summary_product']
    
    # Format for display
    display_df = summary_product.copy()
    for col in ['TONG_T1', 'TONG_T2', 'TONG_DELTA']:
        display_df[col] = display_df[col].apply(lambda x: f"{x:,.0f}")
    
    st.dataframe(display_df, use_container_width=True)
    
    # Chart
    if not summary_product.empty:
        fig = px.bar(
            summary_product,
            x='DP_GROUP',
            y='TONG_DELTA',
            title='Biến Động Theo Nhóm Sản Phẩm',
            color='TONG_DELTA',
            color_continuous_scale=['red', 'yellow', 'green']
        )
        st.plotly_chart(fig, use_container_width=True)


def tab_outliers(data):
    """Display outliers."""
    st.header("🚨 Phát Hiện Bất Thường")
    
    st.warning("""
    ⚠️ **Bất Thường (Outlier)** là những giao dịch có chênh lệch bất thường so với trung bình.
    Hệ thống sử dụng phương pháp **IQR (Interquartile Range)** để phát hiện.
    """)
    
    outliers = data['outliers']
    
    if outliers.empty:
        st.success("✅ Không phát hiện bất thường nào")
    else:
        # Display outliers
        display_df = outliers.copy()
        for col in ['TOTAL_T1', 'TOTAL_T2', 'DELTA']:
            if col in display_df.columns:
                display_df[col] = display_df[col].apply(lambda x: f"{x:,.0f}")
        
        cols_to_show = ['MA_CN', 'MA_KH', 'TEN_KH', 'CUST_TYPE_NAME', 'TOTAL_T1', 'TOTAL_T2', 'DELTA', 'BIEN_DONG']
        display_df = display_df[[col for col in cols_to_show if col in display_df.columns]]
        
        st.dataframe(display_df, use_container_width=True, height=400)
        
        # Statistics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Tổng Bất Thường", len(outliers))
        with col2:
            positive = len(outliers[outliers['DELTA'] > 0])
            st.metric("Tăng Bất Thường", positive)
        with col3:
            negative = len(outliers[outliers['DELTA'] < 0])
            st.metric("Giảm Bất Thường", negative)


def tab_charts(data):
    """Display charts."""
    st.header("📈 Biểu Đồ")
    
    comparison_df = data['comparison']
    summary_branch = data['summary_branch']
    summary_cust = data['summary_cust_type']
    summary_product = data['summary_product']
    
    col1, col2 = st.columns(2)
    
    # Chart 1: Growth by branch
    with col1:
        if not summary_branch.empty:
            fig = px.bar(
                summary_branch.sort_values('TONG_DELTA', ascending=False),
                x='MA_CN',
                y='TONG_DELTA',
                title='Tăng Trưởng Theo Chi Nhánh',
                color='TONG_DELTA',
                color_continuous_scale=['red', 'yellow', 'green']
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Chart 2: Customer type comparison
    with col2:
        if not summary_cust.empty:
            fig = px.pie(
                summary_cust,
                names='CUST_TYPE_NAME',
                values='TONG_DELTA',
                title='Tỷ Lệ DELTA Theo Phân Khúc'
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Chart 3: Product group
    col3, col4 = st.columns(2)
    with col3:
        if not summary_product.empty:
            fig = px.bar(
                summary_product.sort_values('TONG_DELTA', ascending=False),
                x='DP_GROUP',
                y=['TONG_T1', 'TONG_T2'],
                barmode='group',
                title='So Sánh Theo Nhóm Sản Phẩm'
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Chart 4: Change type distribution
    with col4:
        change_summary = data['summary_change']
        if not change_summary.empty:
            fig = px.bar(
                change_summary,
                x='BIEN_DONG',
                y='SO_KH',
                title='Phân Bố Biến Động Khách Hàng',
                color='BIEN_DONG'
            )
            st.plotly_chart(fig, use_container_width=True)


def tab_export(data):
    """Export functionality."""
    st.header("💾 Xuất Báo Cáo Excel")
    
    st.info("""
    📌 **Tính Năng Xuất Báo Cáo:**
    - Xuất toàn bộ dữ liệu so sánh sang 5 sheet Excel
    - Định dạng chuyên nghiệp với header màu
    - Hỗ trợ công thức và định dạng số tiền
    """)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("📥 Tải Xuống Excel Báo Cáo Đầy Đủ", use_container_width=True, type="primary"):
            try:
                with st.spinner("⏳ Đang chuẩn bị file Excel..."):
                    excel_data = export_to_excel(
                        data['comparison'],
                        data['summary_branch'],
                        data['summary_cust_type'],
                        data['summary_product'],
                        data['outliers']
                    )
                    
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"BaoCao_SoSanh_TienGui_{timestamp}.xlsx"
                    
                    st.download_button(
                        label="💾 Tải Xuống",
                        data=excel_data,
                        file_name=filename,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                    
                    st.success(f"✅ File sẵn sàng: {filename}")
            except Exception as e:
                st.error(f"❌ Lỗi xuất báo cáo: {str(e)}")
    
    st.divider()
    
    # Sheet descriptions
    st.subheader("📋 Nội Dung Báo Cáo")
    
    tabs_info = st.tabs([
        "📊 Chi Tiết Khách Hàng",
        "🏢 Theo Chi Nhánh",
        "👥 Theo Phân Khúc",
        "📦 Theo Sản Phẩm",
        "⚠️ Bất Thường"
    ])
    
    with tabs_info[0]:
        st.markdown("""
        **Danh sách tất cả khách hàng với:**
        - Mã khách hàng, tên khách hàng
        - Dư tiền T1 và T2
        - Chênh lệch (DELTA)
        - Loại biến động
        
        **Dùng để:** Phân tích chi tiết từng giao dịch
        """)
    
    with tabs_info[1]:
        st.markdown("""
        **Thống kê tổng hợp theo chi nhánh:**
        - Tổng dư T1 và T2
        - Tổng chênh lệch
        - Tỷ lệ tăng trưởng (%)
        
        **Dùng để:** So sánh hiệu suất giữa các chi nhánh
        """)
    
    with tabs_info[2]:
        st.markdown("""
        **Thống kê theo phân khúc khách:**
        - Cá Nhân vs Pháp Nhân
        - Số lượng khách hàng
        - Tổng dư tiền theo phân khúc
        
        **Dùng để:** Phân tích hành vi từng khúc thị trường
        """)
    
    with tabs_info[3]:
        st.markdown("""
        **Thống kê theo loại sản phẩm:**
        - Từng loại sản phẩm gửi
        - Tổng dư và chênh lệch
        - Số khách sử dụng
        
        **Dùng để:** Đánh giá hiệu suất sản phẩm
        """)
    
    with tabs_info[4]:
        st.markdown("""
        **Danh sách các giao dịch bất thường:**
        - Change lớn hơn kỳ vọng (IQR)
        - Chi tiết khách hàng
        - Mức biến động
        
        **Dùng để:** Phát hiện giao dịch cần kiểm tra
        """)


if __name__ == "__main__":
    main()
