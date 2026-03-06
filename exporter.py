"""
Export module for generating Excel reports.
"""
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from datetime import datetime
import io


def format_currency(value):
    """Format value as currency."""
    if pd.isna(value):
        return 0
    return f"{value:,.0f}"


def format_percentage(value):
    """Format value as percentage."""
    if pd.isna(value):
        return "0%"
    return f"{value:.2%}"


def apply_header_style(worksheet, header_row: int):
    """Apply styling to header row."""
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF")
    
    for cell in worksheet[header_row]:
        if cell.value:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)


def apply_data_style(worksheet, start_row: int, end_row: int):
    """Apply styling to data rows."""
    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    for row in worksheet.iter_rows(min_row=start_row, max_row=end_row):
        for cell in row:
            cell.border = thin_border
            cell.alignment = Alignment(horizontal="center", vertical="center")


def export_to_excel(
    comparison_df: pd.DataFrame,
    summary_branch: pd.DataFrame,
    summary_cust_type: pd.DataFrame,
    summary_product: pd.DataFrame,
    outliers_df: pd.DataFrame,
    filename: str = None
) -> bytes:
    """
    Export all data to Excel with multiple sheets.
    Optimized for speed with minimal styling.
    
    Args:
        comparison_df: Detailed comparison data
        summary_branch: Summary by branch
        summary_cust_type: Summary by customer type
        summary_product: Summary by product group
        outliers_df: Outlier data
        filename: Output filename (optional)
        
    Returns:
        Excel file as bytes
    """
    output = io.BytesIO() if not filename else None
    writer_path = output if output else filename
    
    with pd.ExcelWriter(writer_path, engine='openpyxl') as writer:
        # Sheet 1: Detailed customers
        if not comparison_df.empty:
            df_export = comparison_df.copy()
            # Format numeric columns efficiently
            for col in ['TOTAL_T1', 'TOTAL_T2', 'DELTA']:
                if col in df_export.columns:
                    df_export[col] = df_export[col].apply(lambda x: f"{x:,.0f}" if pd.notna(x) else "0")
            
            df_export.to_excel(writer, sheet_name='Chi Tiết Khách Hàng', index=False)
            
            # Minimal header styling
            ws = writer.sheets['Chi Tiết Khách Hàng']
            header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
            header_font = Font(bold=True, color="FFFFFF")
            
            for cell in ws[1]:
                cell.fill = header_fill
                cell.font = header_font
            
            # Set fixed column widths for speed
            for col_num, column_title in enumerate(df_export.columns, 1):
                col_letter = get_column_letter(col_num)
                ws.column_dimensions[col_letter].width = 15
        
        # Sheet 2: Summary by branch
        if not summary_branch.empty:
            df_export = summary_branch.copy()
            for col in ['TONG_T1', 'TONG_T2', 'TONG_DELTA']:
                if col in df_export.columns:
                    df_export[col] = df_export[col].apply(lambda x: f"{x:,.0f}" if pd.notna(x) else "0")
            if 'TY_LE_TANG_TRUONG' in df_export.columns:
                df_export['TY_LE_TANG_TRUONG'] = df_export['TY_LE_TANG_TRUONG'].apply(lambda x: f"{x:.2%}" if pd.notna(x) else "0%")
            
            df_export.to_excel(writer, sheet_name='Theo Chi Nhánh', index=False)
            
            ws = writer.sheets['Theo Chi Nhánh']
            for cell in ws[1]:
                cell.fill = header_fill
                cell.font = header_font
            for col_num in range(1, len(df_export.columns) + 1):
                ws.column_dimensions[get_column_letter(col_num)].width = 18
        
        # Sheet 3: Summary by customer type
        if not summary_cust_type.empty:
            df_export = summary_cust_type.copy()
            for col in ['TONG_T1', 'TONG_T2', 'TONG_DELTA']:
                if col in df_export.columns:
                    df_export[col] = df_export[col].apply(lambda x: f"{x:,.0f}" if pd.notna(x) else "0")
            
            df_export.to_excel(writer, sheet_name='Theo Phân Khúc', index=False)
            
            ws = writer.sheets['Theo Phân Khúc']
            for cell in ws[1]:
                cell.fill = header_fill
                cell.font = header_font
            for col_num in range(1, len(df_export.columns) + 1):
                ws.column_dimensions[get_column_letter(col_num)].width = 18
        
        # Sheet 4: Summary by product group
        if not summary_product.empty:
            df_export = summary_product.copy()
            for col in ['TONG_T1', 'TONG_T2', 'TONG_DELTA']:
                if col in df_export.columns:
                    df_export[col] = df_export[col].apply(lambda x: f"{x:,.0f}" if pd.notna(x) else "0")
            
            df_export.to_excel(writer, sheet_name='Theo Sản Phẩm', index=False)
            
            ws = writer.sheets['Theo Sản Phẩm']
            for cell in ws[1]:
                cell.fill = header_fill
                cell.font = header_font
            for col_num in range(1, len(df_export.columns) + 1):
                ws.column_dimensions[get_column_letter(col_num)].width = 18
        
        # Sheet 5: Outliers
        if not outliers_df.empty:
            df_export = outliers_df.copy()
            for col in ['TOTAL_T1', 'TOTAL_T2', 'DELTA']:
                if col in df_export.columns:
                    df_export[col] = df_export[col].apply(lambda x: f"{x:,.0f}" if pd.notna(x) else "0")
            
            outlier_cols = ['MA_CN', 'MA_KH', 'TEN_KH', 'CUST_TYPE_NAME', 'TOTAL_T1', 'TOTAL_T2', 'DELTA', 'BIEN_DONG']
            df_export = df_export[[col for col in outlier_cols if col in df_export.columns]]
            
            df_export.to_excel(writer, sheet_name='Bất Thường', index=False)
            
            ws = writer.sheets['Bất Thường']
            for cell in ws[1]:
                cell.fill = header_fill
                cell.font = header_font
            for col_num in range(1, len(df_export.columns) + 1):
                ws.column_dimensions[get_column_letter(col_num)].width = 15
    
    if output:
        output.seek(0)
        return output.getvalue()
    
    return None
