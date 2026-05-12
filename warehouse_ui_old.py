"""
UI components for warehouse-based comparison workflow.
"""

import streamlit as st
import pandas as pd
import tempfile
import os
from data_warehouse import (
    import_files_batch, list_warehouse_files, delete_warehouse_files_batch,
    get_warehouse_stats, get_file_path, get_file_info
)
from loader import load_and_normalize_csv, filter_valid_data
from aggregator import aggregate_pair
from compare_engine import merge_and_compare

def render_warehouse_modal():
    """Render warehouse management in a modal dialog."""
    if 'show_warehouse_modal' not in st.session_state:
        st.session_state.show_warehouse_modal = False
    
    # Button to open modal
    col1, col2 = st.columns([0.3, 0.7])
    with col1:
        if st.button('🗂️ Quản Lý Kho Dữ Liệu', use_container_width=True, key='open_warehouse_modal'):
            st.session_state.show_warehouse_modal = True
    
    # Modal display with enhanced styling
    if st.session_state.show_warehouse_modal:
        # Add custom CSS for modal styling
        st.markdown("""
        <style>
        .modal-container {
            position: relative;
            background: white;
            border: 2px solid #1f77b4;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1), 0 1px 3px rgba(0, 0, 0, 0.08);
            margin: 20px 0;
        }
        .modal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            border-bottom: 2px solid #f0f0f0;
            padding-bottom: 15px;
        }
        .modal-title {
            font-size: 1.5em;
            font-weight: 600;
            color: #1f77b4;
        }
        .modal-close-btn {
            font-size: 1.5em;
            cursor: pointer;
            color: #666;
            transition: color 0.2s;
        }
        .modal-close-btn:hover {
            color: #000;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Modal container
        with st.container(border=True):
            # Modal header with close button
            col_title, col_close = st.columns([0.95, 0.05])
            with col_title:
                st.markdown("### 🗂️ Quản Lý Kho Dữ Liệu")
            with col_close:
                if st.button('✕', key='close_warehouse_modal', help='Đóng', use_container_width=False):
                    st.session_state.show_warehouse_modal = False
                    st.rerun()
            
            st.divider()
            
            # Tabs for different management sections
            tab1, tab2 = st.tabs(['📁 Các File', '📤 Import Mới'])
            
            with tab1:
                warehouse_files = list_warehouse_files()
                warehouse_stats = get_warehouse_stats()
                
                # Stats row
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric('📁 Tổng Files', warehouse_stats['total_files'])
                with col2:
                    st.metric('🏢 Chi Nhánh', warehouse_stats['total_branches'])
                with col3:
                    st.metric('💾 Dung Lượng', f"{warehouse_stats['total_size'] / (1024*1024):.1f} MB")
                
                st.divider()
                
                if warehouse_files.empty:
                    st.info('📭 Kho dữ liệu trống. Hãy import file từ tab "📤 Import Mới".')
                else:
                    # Display files with better formatting
                    st.subheader('📋 Danh sách file')
                    display_df = warehouse_files[['original_name', 'branch_code', 'import_date', 'file_size']].copy()
                    display_df.columns = ['📄 Tên File', '🏢 Chi Nhánh', '📅 Ngày Import', '📊 Size (bytes)']
                    st.dataframe(display_df, use_container_width=True, hide_index=True)
                    
                    st.divider()
                    
                    # Delete section
                    st.subheader('🗑️ Xóa File')
                    delete_ids = st.multiselect(
                        'Chọn file để xóa:',
                        options=warehouse_files['id'].tolist(),
                        format_func=lambda x: warehouse_files[warehouse_files['id'] == x]['original_name'].values[0],
                        key='files_to_delete'
                    )
                    
                    if delete_ids:
                        st.warning(f'⚠️ Bạn sắp xóa {len(delete_ids)} file. Hành động này không thể hoàn tác.')
                        col1, col2 = st.columns([0.7, 0.3])
                        with col2:
                            if st.button('🗑️ Xóa Ngay', type='secondary', key='warehouse_confirm_delete_btn', use_container_width=True):
                                result = delete_warehouse_files_batch(delete_ids)
                                if result['deleted']:
                                    st.success(f"✅ Xóa {len(result['deleted'])} file thành công")
                                if result['errors']:
                                    st.error(f"❌ Lỗi: {result['errors']}")
                                st.rerun()
            
            with tab2:
                st.subheader('📤 Import Files Mới')
                st.caption('Chọn file CSV để import vào kho dữ liệu.')
                
                upload_files = st.file_uploader(
                    'Chọn file(s) CSV',
                    type='csv',
                    accept_multiple_files=True,
                    key='warehouse_upload',
                )
                
                if upload_files:
                    st.info(f'📌 Đã chọn {len(upload_files)} file')
                    if st.button('✅ Import vào Kho', use_container_width=True, type='primary', key='warehouse_import_btn'):
                        try:
                            from app import save_uploaded_files, cleanup_temp_dir
                            # Save to temp directory first
                            temp_dir = tempfile.mkdtemp()
                            temp_paths = save_uploaded_files(upload_files, temp_dir)
                            
                            # Import each file to warehouse
                            with st.spinner('Đang import file...'):
                                results = import_files_batch(temp_paths)
                            
                            # Clean up temp files
                            cleanup_temp_dir(temp_dir)
                            
                            # Show results
                            if results['imported']:
                                st.success(f"✅ Import thành công {len(results['imported'])} file")
                            if results['duplicates']:
                                st.info(f"📋 {len(results['duplicates'])} file đã tồn tại trong kho")
                            if results['errors']:
                                st.error(f"❌ Lỗi với {len(results['errors'])} file")
                                for err in results['errors']:
                                    st.write(f"  • {err['file']}: {err['error']}")
                            
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Lỗi: {str(e)}")



def render_warehouse_sidebar(mapping_callback):
    """Render warehouse file selection in sidebar."""
    
    # Import files section  
    with st.expander('📦 1️⃣ Import Files vào Kho Dữ Liệu', expanded=True):
        st.caption('Chọn file CSV để import vào kho dữ liệu. Mỗi file sẽ được lưu trữ và có thể sử dụng lại.')
        
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
                    # Save to temp directory first
                    temp_dir = tempfile.mkdtemp()
                    temp_paths = save_uploaded_files(upload_files, temp_dir)
                    
                    # Import each file to warehouse
                    with st.spinner('Đang import file...'):
                        results = import_files_batch(temp_paths)
                    
                    # Clean up temp files
                    cleanup_temp_dir(temp_dir)
                    
                    # Show results
                    if results['imported']:
                        st.success(f"✅ Import thành công {len(results['imported'])} file")
                    if results['duplicates']:
                        st.info(f"📋 {len(results['duplicates'])} file đã tồn tại trong kho")
                    if results['errors']:
                        st.error(f"❌ Lỗi với {len(results['errors'])} file")
                        for err in results['errors']:
                            st.write(f"  • {err['file']}: {err['error']}")
                    
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Lỗi: {str(e)}")

    # File selection for comparison
    with st.expander('📊 2️⃣ Chọn Files để So Sánh', expanded=True):
        st.caption('Chọn T1 files và T2 files từ kho để so sánh.')
        
        warehouse_files = list_warehouse_files()
        
        if warehouse_files.empty:
            st.warning('⚠️ Kho dữ liệu trống. Vui lòng import file ở bước 1.')
            return None, None, False
        else:
            st.write('**Chọn T1 (Dữ liệu Cũ / Quý Trước):**')
            t1_selected = st.multiselect(
                'T1 Files:',
                options=warehouse_files['id'].tolist(),
                format_func=lambda x: warehouse_files[warehouse_files['id'] == x]['original_name'].values[0],
                key='t1_selection',
                label_visibility='collapsed'
            )
            
            st.write('**Chọn T2 (Dữ liệu Mới / Quý Hiện Tại):**')
            t2_selected = st.multiselect(
                'T2 Files:',
                options=warehouse_files['id'].tolist(),
                format_func=lambda x: warehouse_files[warehouse_files['id'] == x]['original_name'].values[0],
                key='t2_selection',
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
                    st.success(f'✅ Đã chọn {t1_count} file cho T1 và T2')
                    valid_pair = True
            
            return t1_selected, t2_selected, valid_pair


def build_comparison_from_warehouse(t1_ids, t2_ids, column_mapping):
    """Build comparison data from warehouse file IDs."""
    
    # Get file paths
    t1_paths = [get_file_path(fid) for fid in t1_ids if get_file_path(fid)]
    t2_paths = [get_file_path(fid) for fid in t2_ids if get_file_path(fid)]
    
    if not t1_paths or not t2_paths:
        raise ValueError("Some files cannot be found in warehouse")
    
    # Process similar to original flow
    all_raw_data = {}
    comparison_results = []
    
    # Sort by filename to match branches
    t1_by_name = {os.path.basename(p): p for p in sorted(t1_paths)}
    t2_by_name = {os.path.basename(p): p for p in sorted(t2_paths)}
    
    # Match files by branch code
    for t1_name in t1_by_name.keys():
        # Extract branch code from filename (first 4 chars before _dp01)
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
    import pandas as pd
    comparison_df = pd.concat(comparison_results, ignore_index=True) if comparison_results else pd.DataFrame()
    
    return {
        'comparison': comparison_df,
        'all_raw_data': all_raw_data,
        't1_paths': t1_paths,
        't2_paths': t2_paths,
    }
