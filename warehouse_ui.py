"""
Enhanced UI components for warehouse management with date selection and advanced features.
Includes: validation, versioning, auto-matching, and file-based date selection.
"""

import streamlit as st
import pandas as pd
import tempfile
import os
from datetime import datetime, timedelta
from data_warehouse import (
    import_files_batch, list_warehouse_files, delete_warehouse_file, delete_warehouse_files_batch,
    get_warehouse_stats, get_file_path, get_file_info, update_file_validation_status, 
    get_validation_status, suggest_file_pairs, get_file_statistics
)
from loader import load_and_normalize_csv, filter_valid_data
from aggregator import aggregate_pair
from compare_engine import merge_and_compare
from auth_manager import log_audit


def _audit(action, target_type=None, target_id=None, branch_code=None, details=''):
    log_audit('SYSTEM', action, target_type, target_id, branch_code, details)


def render_warehouse_modal():
    """Render enhanced warehouse management modal with all features."""
    if 'show_warehouse_modal' not in st.session_state:
        st.session_state.show_warehouse_modal = False
    
    # Button to open modal
    col1, col2 = st.columns([0.3, 0.7])
    with col1:
        if st.button('🗂️ Quản Lý Kho Dữ Liệu', use_container_width=True, key='open_warehouse_modal'):
            st.session_state.show_warehouse_modal = True
    
    if st.session_state.show_warehouse_modal:
        with st.container(border=True):
            # Header with close button
            col_title, col_close = st.columns([0.95, 0.05])
            with col_title:
                st.markdown("### 🗂️ Quản Lý Kho Dữ Liệu")
            with col_close:
                if st.button('✕', key='close_warehouse_modal', help='Đóng'):
                    st.session_state.show_warehouse_modal = False
                    st.rerun()
            
            st.divider()
            
            # Main tabs
            tab_calendar, tab_list, tab_import, tab_stats = st.tabs([
                '📅 Ngày Dữ Liệu', 
                '📋 Danh Sách Files',
                '📤 Import Mới',
                '📊 Thống Kê'
            ])
            
            with tab_calendar:
                render_calendar_view()
            
            with tab_list:
                render_enhanced_file_list()
            
            with tab_import:
                render_import_section()
            
            with tab_stats:
                render_statistics_section()


def render_calendar_view():
    """Render date selection file view."""
    st.subheader('📅 Xem Files theo Ngày')
    st.caption('Chọn ngày dữ liệu theo tên file; chỉ hiển thị những ngày có file.')
    
    warehouse_files = list_warehouse_files()
    
    if warehouse_files.empty:
        st.info('📭 Kho dữ liệu trống.')
        return
    
    # Use business data date from file name, not import timestamp
    warehouse_files['data_date'] = pd.to_datetime(warehouse_files['data_date'], errors='coerce')
    warehouse_files = warehouse_files.dropna(subset=['data_date']).copy()
    warehouse_files['date_only'] = warehouse_files['data_date'].dt.date
    
    files_by_date = warehouse_files.groupby('date_only').size()
    date_counts = files_by_date.to_dict()
    available_dates = sorted(date_counts.keys())
    if not available_dates:
        st.info('Chưa có ngày dữ liệu hợp lệ trong kho.')
        return

    # Create date selection area with only available data dates
    col1, col2 = st.columns([0.45, 0.55])
    with col1:
        selected_date = st.selectbox(
            'Chọn ngày dữ liệu:',
            options=available_dates,
            format_func=lambda d: f"{d.strftime('%d/%m/%Y')} ({date_counts.get(d, 0)} file)",
            index=len(available_dates) - 1,
            key='calendar_date_selector'
        )
        st.caption('Chọn một ngày thực sự có dữ liệu; không hiển thị ngày trống.')

    with col2:
        # Files on selected business date
        selected_files = warehouse_files[warehouse_files['date_only'] == selected_date]
        
        if not selected_files.empty:
            branch_count = selected_files['branch_code'].nunique() if 'branch_code' in selected_files.columns else len(selected_files)
            st.success(f"📁 {len(selected_files)} file dữ liệu cho ngày {selected_date.strftime('%d/%m/%Y')} ({branch_count} chi nhánh)")
            
            for idx, file in selected_files.iterrows():
                with st.container(border=True):
                    col1, col2 = st.columns([0.8, 0.2])
                    
                    with col1:
                        st.write(f"**📄 {file['original_name']}**")
                        cols = st.columns(4)
                        cols[0].caption(f"🏢 {file['branch_code']}")
                        cols[1].caption(f"📊 {file['record_count']} records")
                        cols[2].caption(f"💾 {file['file_size'] / 1024:.1f} KB")
                        import_time = pd.to_datetime(file['import_date'], errors='coerce')
                        cols[3].caption(f"⏰ {import_time.strftime('%H:%M') if not pd.isna(import_time) else 'N/A'}")
                    
                    with col2:
                        render_file_actions(file['id'], idx, context='calendar')
        else:
            st.info(f'No files on {selected_date}')
    
    st.divider()
    
    # Timeline view based on business data date
    st.subheader('📈 Timeline')
    if not files_by_date.empty:
        st.bar_chart(files_by_date, height=200)


def render_enhanced_file_list():
    """Render enhanced file list with search, filter, tags, and batch operations."""
    warehouse_files = list_warehouse_files()
    warehouse_stats = get_warehouse_stats()
    
    # Stats row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric('📁 Tổng Files', warehouse_stats['total_files'])
    with col2:
        st.metric('🏢 Chi Nhánh', warehouse_stats['total_branches'])
    with col3:
        st.metric('💾 Dung Lượng', f"{warehouse_stats['total_size'] / (1024*1024):.1f} MB")
    with col4:
        # Calculate total records
        total_records = warehouse_files['record_count'].sum() if not warehouse_files.empty else 0
        st.metric('📊 Tổng Records', f"{total_records:,}")
    
    st.divider()
    
    if warehouse_files.empty:
        st.info('📭 Kho dữ liệu trống.')
        return
    
    # Search and filter section
    col1, col2 = st.columns(2)
    
    with col1:
        search_query = st.text_input('🔍 Tìm kiếm file:', placeholder='Nhập tên file...')
    
    with col2:
        selected_branches = st.multiselect(
            '🏢 Lọc theo chi nhánh:',
            options=sorted(warehouse_files['branch_code'].dropna().unique()),
            key='branch_filter'
        )
    
    # Apply filters
    filtered_files = warehouse_files.copy()
    
    if search_query:
        filtered_files = filtered_files[
            filtered_files['original_name'].str.contains(search_query, case=False, na=False)
        ]
    
    if selected_branches:
        filtered_files = filtered_files[filtered_files['branch_code'].isin(selected_branches)]
    
    st.divider()
    
    # Display filtered files with pagination
    if filtered_files.empty:
        st.info('No files matching your filters.')
    else:
        st.subheader(f'📋 Danh sách ({len(filtered_files)} files)')
        
        # Batch operations
        col1, col2 = st.columns([0.8, 0.2])
        with col2:
            if st.checkbox('🗑️ Mode xóa', key='delete_mode_enhanced'):
                delete_ids = st.multiselect(
                    'Chọn file để xóa:',
                    options=filtered_files['id'].tolist(),
                    format_func=lambda x: filtered_files[filtered_files['id'] == x]['original_name'].values[0],
                    key='enhanced_delete_ids'
                )
                
                if delete_ids:
                    st.warning(f'⚠️ Sắp xóa {len(delete_ids)} file.')
                    if st.button('🗑️ Xóa', type='secondary', key='confirm_enhanced_delete'):
                        result = delete_warehouse_files_batch(delete_ids)
                        if result['deleted']:
                            _audit('WAREHOUSE_DELETE', 'warehouse_file', None, None, f"Deleted {len(result['deleted'])} file(s): {delete_ids}")
                            st.success(f"✅ Xóa {len(result['deleted'])} file thành công")
                        st.rerun()
        
        # Pagination logic
        files_per_page = 8
        total_files = len(filtered_files)
        total_pages = (total_files + files_per_page - 1) // files_per_page
        
        if 'file_list_page' not in st.session_state:
            st.session_state.file_list_page = 0
        
        current_page = st.session_state.file_list_page
        if current_page >= total_pages:
            current_page = max(0, total_pages - 1)
            st.session_state.file_list_page = current_page
        
        # Pagination controls
        col1, col2, col3, col4, col5 = st.columns([0.2, 0.2, 0.2, 0.2, 0.2])
        with col1:
            if st.button('⬅️ Trang Trước', use_container_width=True, disabled=current_page == 0):
                st.session_state.file_list_page = max(0, current_page - 1)
                st.rerun()
        with col2:
            st.write('')
        with col3:
            st.caption(f'📄 Trang {current_page + 1}/{total_pages}')
        with col4:
            st.write('')
        with col5:
            if st.button('Trang Sau ➡️', use_container_width=True, disabled=current_page >= total_pages - 1):
                st.session_state.file_list_page = min(total_pages - 1, current_page + 1)
                st.rerun()
        
        st.divider()
        
        # Display files for current page
        start_idx = current_page * files_per_page
        end_idx = min(start_idx + files_per_page, total_files)
        page_files = filtered_files.iloc[start_idx:end_idx]
        
        for local_idx, (idx, file) in enumerate(page_files.iterrows()):
            render_file_detail_card(file, start_idx + local_idx, context='list')


def render_file_detail_card(file, index=0, context='list'):
    """Render a detailed card for a single file."""
    with st.container(border=True):
        col1, col2, col3 = st.columns([0.6, 0.2, 0.2])
        
        # Main info
        with col1:
            st.write(f"**📄 {file['original_name']}**")
            
            # Validation status
            validation_status = get_validation_status(file['id'])
            status_icon = '✅' if validation_status == 'valid' else '⚠️' if validation_status == 'warning' else '❓'
            st.caption(f"{status_icon} Status: {validation_status}")
            
            # File details
            detail_cols = st.columns(4)
            detail_cols[0].caption(f"🏢 {file['branch_code']}")
            detail_cols[1].caption(f"📊 {file['record_count']} records")
            detail_cols[2].caption(f"💰 {file['total_balance'] / 1_000_000:.1f}M VND" if file['total_balance'] else "💰 N/A")
            detail_cols[3].caption(f"📅 {pd.to_datetime(file['import_date']).strftime('%d/%m/%Y')}")
            
            # Additional stats
            if file['avg_balance']:
                stat_cols = st.columns(3)
                stat_cols[0].caption(f"📈 Avg: {file['avg_balance'] / 1_000_000:.1f}M")
                stat_cols[1].caption(f"📊 Min: {file['min_balance'] / 1_000_000:.1f}M" if file['min_balance'] else "Min: N/A")
                stat_cols[2].caption(f"🔝 Max: {file['max_balance'] / 1_000_000:.1f}M" if file['max_balance'] else "Max: N/A")
        
        # Size info
        with col2:
            st.metric('Size', f"{file['file_size'] / 1024:.1f} KB")
        
        # Actions
        with col3:
            render_file_actions(file['id'], index)


def render_file_actions(file_id, index=0, context='list'):
    """Render action buttons for a file."""
    prefix = f'{context}_' if context else ''
    col1, col2 = st.columns([0.5, 0.5])
    
    with col1:
        if st.button('ℹ️ Chi tiết', key=f'{prefix}info_{file_id}_{index}', use_container_width=True):
            st.session_state[f'{prefix}show_details_{file_id}'] = not st.session_state.get(f'{prefix}show_details_{file_id}', False)

    with col2:
        if st.button('🗑️ Xóa', key=f'{prefix}delete_{file_id}_{index}', use_container_width=True):
            message = delete_warehouse_file(file_id)
            st.success(message)
            st.experimental_rerun()
    
    # Show details if toggled
    if st.session_state.get(f'{prefix}show_details_{file_id}', False):
        file_info = get_file_info(file_id)
        if file_info:
            st.json(file_info)


def render_import_section():
    """Render import section in modal."""
    st.subheader('📤 Import Files Mới')
    st.caption('Chọn file CSV để import vào kho dữ liệu.')
    
    upload_files = st.file_uploader(
        'Chọn file(s) CSV',
        type='csv',
        accept_multiple_files=True,
        key='warehouse_upload_modal',
    )
    
    if upload_files:
        st.info(f'📌 Đã chọn {len(upload_files)} file')
        
        if st.button('✅ Import vào Kho', use_container_width=True, type='primary', key='modal_import_btn'):
            try:
                from app import save_uploaded_files, cleanup_temp_dir
                
                temp_dir = tempfile.mkdtemp()
                temp_paths = save_uploaded_files(upload_files, temp_dir)
                
                with st.spinner('Đang import file...'):
                    results = import_files_batch(temp_paths)
                
                cleanup_temp_dir(temp_dir)
                
                # Show errors first (most important)
                if results['errors']:
                    st.error(f"❌ Lỗi import ({len(results['errors'])} file):")
                    for err in results['errors']:
                        st.error(f"📄 {err['file']}:\n{err['error']}")
                    st.divider()
                
                # Show duplicates (warnings)
                if results['duplicates']:
                    st.warning(f"⚠️ File đã tồn tại ({len(results['duplicates'])} file):")
                    for dup in results['duplicates']:
                        st.warning(f"📄 {dup['file']} (ID: {dup['id']})")
                    st.divider()
                
                # Show success last (positive news)
                if results['imported']:
                    _audit('WAREHOUSE_IMPORT', 'warehouse_file', None, None, f"Imported {len(results['imported'])} file(s)")
                    st.success(f"✅ Import thành công {len(results['imported'])} file")
                    for imported in results['imported']:
                        st.success(f"📄 {imported['file']} (ID: {imported['id']})")
                
                # Only rerun if there are no errors
                if not results['errors']:
                    st.rerun()
            except Exception as e:
                st.error(f"❌ Lỗi hệ thống:\n{str(e)}")


def render_statistics_section():
    """Render advanced statistics."""
    st.subheader('📊 Thống Kê Kho Dữ Liệu')
    
    stats = get_file_statistics()
    
    # By branch
    st.subheader('Chi Nhánh')
    if stats['by_branch']:
        branch_df = pd.DataFrame([
            {'Chi Nhánh': branch, 'Số Files': info['count'], 'Tổng Records': info['records']}
            for branch, info in stats['by_branch'].items()
        ])
        st.dataframe(branch_df, use_container_width=True, hide_index=True)
    else:
        st.info('Chưa có dữ liệu chi nhánh.')


def render_warehouse_sidebar(mapping_callback):
    """Render warehouse file selection in sidebar with auto-matching."""
    
    # Import files section  
    with st.expander('📦 1️⃣ Import Files vào Kho Dữ Liệu', expanded=True):
        st.caption('Chọn file CSV để import vào kho dữ liệu.')
        
        upload_files = st.file_uploader(
            'Chọn file(s) CSV để import',
            type='csv',
            accept_multiple_files=True,
            key='warehouse_upload_main',
        )
        
        if upload_files:
            if st.button('✅ Import vào Kho', use_container_width=True, type='primary', key='warehouse_import_btn_main'):
                try:
                    from app import save_uploaded_files, cleanup_temp_dir
                    
                    temp_dir = tempfile.mkdtemp()
                    temp_paths = save_uploaded_files(upload_files, temp_dir)
                    
                    with st.spinner('Đang import file...'):
                        results = import_files_batch(temp_paths)
                    
                    cleanup_temp_dir(temp_dir)
                    
                    # Show errors first (most important)
                    if results['errors']:
                        st.error(f"❌ Lỗi import ({len(results['errors'])} file):")
                        for err in results['errors']:
                            st.error(f"📄 {err['file']}:\n{err['error']}")
                        st.divider()
                    
                    # Show duplicates (warnings)
                    if results['duplicates']:
                        st.warning(f"⚠️ File đã tồn tại ({len(results['duplicates'])} file):")
                        for dup in results['duplicates']:
                            st.warning(f"📄 {dup['file']} (ID: {dup['id']})")
                        st.divider()
                    
                    # Show success last (positive news)
                    if results['imported']:
                        st.success(f"✅ Import thành công {len(results['imported'])} file")
                        for imported in results['imported']:
                            st.success(f"📄 {imported['file']} (ID: {imported['id']})")
                    
                    # Only rerun if there are no errors
                    if not results['errors']:
                        st.rerun()
                except Exception as e:
                    st.error(f"❌ Lỗi hệ thống:\n{str(e)}")

    # File selection for comparison with auto-matching
    with st.expander('📊 2️⃣ Chọn Files để So Sánh', expanded=True):
        st.caption('Chọn T1 và T2 files. Hệ thống sẽ suggest T2 phù hợp.')
        
        warehouse_files = list_warehouse_files()

        if not warehouse_files.empty and 'data_date' in warehouse_files.columns:
            warehouse_files['data_date'] = pd.to_datetime(warehouse_files['data_date'], errors='coerce')
            dated_files = warehouse_files.dropna(subset=['data_date']).copy()

            if not dated_files.empty:
                dated_files['date_only'] = dated_files['data_date'].dt.date
                available_dates = sorted(dated_files['date_only'].unique(), reverse=True)

                default_t1_index = 1 if len(available_dates) > 1 else 0
                col_t1, col_t2 = st.columns(2)

                with col_t1:
                    t1_date = st.selectbox(
                        'T1 - Ngày dữ liệu cũ:',
                        options=available_dates,
                        index=default_t1_index,
                        format_func=lambda d: d.strftime('%d/%m/%Y'),
                        key='warehouse_t1_data_date',
                    )

                with col_t2:
                    t2_date = st.selectbox(
                        'T2 - Ngày dữ liệu mới:',
                        options=available_dates,
                        index=0,
                        format_func=lambda d: d.strftime('%d/%m/%Y'),
                        key='warehouse_t2_data_date',
                    )

                t1_files = dated_files[dated_files['date_only'] == t1_date]
                t2_files = dated_files[dated_files['date_only'] == t2_date]
                t1_selected = t1_files['id'].tolist()
                t2_selected = t2_files['id'].tolist()

                st.caption(
                    f"T1: {len(t1_selected)} file, {t1_files['branch_code'].nunique()} chi nhánh | "
                    f"T2: {len(t2_selected)} file, {t2_files['branch_code'].nunique()} chi nhánh"
                )

                valid_pair = False
                if t1_selected and t2_selected:
                    t1_branches = set(t1_files['branch_code'].dropna())
                    t2_branches = set(t2_files['branch_code'].dropna())

                    if t1_date == t2_date:
                        st.warning('T1 và T2 đang cùng một ngày dữ liệu.')
                    elif t1_branches != t2_branches:
                        missing_in_t2 = sorted(t1_branches - t2_branches)
                        missing_in_t1 = sorted(t2_branches - t1_branches)
                        if missing_in_t2:
                            st.warning(f"Thiếu trong T2: {', '.join(missing_in_t2)}")
                        if missing_in_t1:
                            st.warning(f"Thiếu trong T1: {', '.join(missing_in_t1)}")
                    else:
                        st.success(f'Đã chọn {len(t1_selected)} cặp file theo ngày dữ liệu.')
                        valid_pair = True

                return t1_selected, t2_selected, valid_pair
        
        if warehouse_files.empty:
            st.warning('⚠️ Kho dữ liệu trống. Vui lòng import file ở bước 1.')
            return None, None, False
        
        # T1 selection
        st.write('**Chọn T1 (Dữ liệu Cũ):**')
        t1_selected = st.multiselect(
            'T1 Files:',
            options=warehouse_files['id'].tolist(),
            format_func=lambda x: warehouse_files[warehouse_files['id'] == x]['original_name'].values[0],
            key='t1_selection_new',
            label_visibility='collapsed'
        )
        
        # Auto-suggest T2
        st.write('**Chọn T2 (Dữ liệu Mới):**')
        if t1_selected:
            suggestions = suggest_file_pairs(t1_selected, warehouse_files)
            st.caption('💡 Gợi ý: Nhấn "Use Suggestions" để áp dụng đề xuất tự động')
            
            col1, col2 = st.columns([0.7, 0.3])
            with col2:
                use_suggestions = st.button('💡 Use Suggestions', key='use_auto_match')
        else:
            suggestions = {}
            use_suggestions = False
        
        # T2 selection
        if use_suggestions and suggestions:
            t2_selected = list(suggestions.values())
            st.success(f'✅ Tự động chọn {len(t2_selected)} file T2')
        else:
            t2_selected = st.multiselect(
                'T2 Files:',
                options=warehouse_files['id'].tolist(),
                format_func=lambda x: warehouse_files[warehouse_files['id'] == x]['original_name'].values[0],
                key='t2_selection_new',
                label_visibility='collapsed'
            )
        
        # Validation
        valid_pair = False
        if t1_selected and t2_selected:
            t1_count = len(t1_selected)
            t2_count = len(t2_selected)
            
            if t1_count != t2_count:
                st.warning(f'⚠️ Số file không khớp: T1 có {t1_count}, T2 có {t2_count}')
            else:
                st.success(f'✅ Đã chọn {t1_count} cặp file (T1 & T2)')
                valid_pair = True
        
        return t1_selected, t2_selected, valid_pair


def build_comparison_from_warehouse(t1_ids, t2_ids, column_mapping):
    """Build comparison data from warehouse file IDs."""
    
    # Get file paths
    t1_file_refs = [(fid, path) for fid in t1_ids if (path := get_file_path(fid))]
    t2_file_refs = [(fid, path) for fid in t2_ids if (path := get_file_path(fid))]
    t1_paths = [path for _, path in t1_file_refs]
    t2_paths = [path for _, path in t2_file_refs]
    
    if not t1_paths or not t2_paths:
        raise ValueError("Some files cannot be found in warehouse")
    
    # Process similar to original flow
    all_raw_data = {}
    comparison_results = []
    
    # Match by original filenames stored in warehouse metadata, not stored hash filenames.
    t1_by_name = {}
    for file_id, path in t1_file_refs:
        info = get_file_info(file_id)
        if info:
            t1_by_name[info['original_name']] = path

    t2_by_name = {}
    for file_id, path in t2_file_refs:
        info = get_file_info(file_id)
        if info:
            t2_by_name[info['original_name']] = path
    
    # Match files by branch code
    for t1_name in t1_by_name.keys():
        if len(t1_name) >= 4 and '_dp01_' in t1_name:
            ma_cn = t1_name[:4]
            
            # Find matching T2 file with same branch
            t2_match = None
            for t2_name in t2_by_name.keys():
                if t2_name.startswith(ma_cn + '_dp01_'):
                    t2_match = t2_by_name[t2_name]
                    break
            
            if t2_match:
                t1_file = t1_by_name[t1_name]
                
                # Load and process
                df_t1 = load_and_normalize_csv(t1_file, column_mapping=column_mapping)
                df_t2 = load_and_normalize_csv(t2_match, column_mapping=column_mapping)
                
                all_raw_data[ma_cn] = {'T1': df_t1, 'T2': df_t2}
                
                # Filter and aggregate
                df_t1_filtered = filter_valid_data(df_t1)
                df_t2_filtered = filter_valid_data(df_t2)
                
                agg_t1, agg_t2 = aggregate_pair(df_t1_filtered, df_t2_filtered)
                
                # Compare
                comparison = merge_and_compare(agg_t1, agg_t2, ma_cn)
                comparison_results.append(comparison)
    
    # Combine all comparisons
    comparison_df = pd.concat(comparison_results, ignore_index=True) if comparison_results else pd.DataFrame()
    
    return {
        'comparison': comparison_df,
        'all_raw_data': all_raw_data,
        't1_paths': t1_paths,
        't2_paths': t2_paths,
    }
