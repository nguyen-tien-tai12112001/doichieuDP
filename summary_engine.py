"""
Summary engine for generating statistics reports.
"""
from typing import Dict, List, Tuple
import pandas as pd


# Mapping of DP_TYPE to product groups
DP_TYPE_MAPPING = {
    '010': 'TIET_KIEM',
    '011': 'TIET_KIEM',
    '012': 'TIET_KIEM',
    '020': 'CO_KY_HAN',
    '021': 'CO_KY_HAN',
    '022': 'CO_KY_HAN',
    '030': 'KHONG_KY_HAN',
    '031': 'KHONG_KY_HAN',
    '032': 'KHONG_KY_HAN',
    '040': 'KHONG_KY_HAN',
    '050': 'CO_KY_HAN',
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


def get_dp_type_mapping() -> Dict[str, str]:
    """
    Get the mapping of DP_TYPE to product groups.
    
    Returns:
        Dict mapping DP_TYPE to DP_GROUP
    """
    return DP_TYPE_MAPPING.copy()


def summary_by_branch(comparison_df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate summary statistics by branch.
    
    Args:
        comparison_df: Comparison DataFrame
        
    Returns:
        Summary by branch
    """
    if comparison_df.empty:
        return pd.DataFrame()
    
    grouped = comparison_df.groupby('MA_CN', as_index=False).agg({
        'TOTAL_T1': 'sum',
        'TOTAL_T2': 'sum',
        'DELTA': 'sum',
        'MA_KH': 'count'
    }).rename(columns={'MA_KH': 'SO_KH'})
    
    # Rename columns for consistency
    grouped = grouped.rename(columns={
        'TOTAL_T1': 'TONG_T1',
        'TOTAL_T2': 'TONG_T2',
        'DELTA': 'TONG_DELTA'
    })
    
    # Calculate growth rate
    grouped['TY_LE_TANG_TRUONG'] = grouped.apply(
        lambda row: (row['TONG_DELTA'] / row['TONG_T1'] * 100) if row['TONG_T1'] != 0 else 0,
        axis=1
    )
    
    return grouped[[
        'MA_CN', 'TONG_T1', 'TONG_T2', 'TONG_DELTA', 'SO_KH', 'TY_LE_TANG_TRUONG'
    ]].sort_values('TONG_DELTA', ascending=False)


def summary_by_customer_type(comparison_df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate summary statistics by customer type.
    
    Args:
        comparison_df: Comparison DataFrame
        
    Returns:
        Summary by customer type
    """
    if comparison_df.empty:
        return pd.DataFrame()
    
    grouped = comparison_df.groupby('CUST_TYPE_NAME', as_index=False).agg({
        'TOTAL_T1': 'sum',
        'TOTAL_T2': 'sum',
        'DELTA': 'sum'
    }).rename(columns={
        'TOTAL_T1': 'TONG_T1',
        'TOTAL_T2': 'TONG_T2',
        'DELTA': 'TONG_DELTA'
    })
    
    return grouped[['CUST_TYPE_NAME', 'TONG_T1', 'TONG_T2', 'TONG_DELTA']]


def summary_by_product_group(all_raw_data: dict) -> pd.DataFrame:
    """
    Generate summary statistics by product group.
    
    Args:
        all_raw_data: Dict {MA_CN: {'T1': df, 'T2': df}} with raw DP_TYPE data
        
    Returns:
        Summary by product group
    """
    mapping = get_dp_type_mapping()
    results = []
    
    # Process T1 data
    for ma_cn, period_data in all_raw_data.items():
        df_t1 = period_data['T1'].copy()
        df_t1['DP_GROUP'] = df_t1['DP_TYPE_CODE'].map(mapping).fillna('OTHER')
        df_t1['PERIOD'] = 'T1'
        
        df_t2 = period_data['T2'].copy()
        df_t2['DP_GROUP'] = df_t2['DP_TYPE_CODE'].map(mapping).fillna('OTHER')
        df_t2['PERIOD'] = 'T2'
        
        results.append(df_t1[['DP_GROUP', 'CURRENT_BALANCE', 'PERIOD']])
        results.append(df_t2[['DP_GROUP', 'CURRENT_BALANCE', 'PERIOD']])
    
    if not results:
        return pd.DataFrame()
    
    combined = pd.concat(results, ignore_index=True)
    
    # Pivot to get T1 and T2 side by side
    pivoted = combined.pivot_table(
        index='DP_GROUP',
        columns='PERIOD',
        values='CURRENT_BALANCE',
        aggfunc='sum',
        fill_value=0
    ).reset_index()
    
    # Rename columns
    if 'T1' in pivoted.columns:
        pivoted = pivoted.rename(columns={'T1': 'TONG_T1'})
    else:
        pivoted['TONG_T1'] = 0
    
    if 'T2' in pivoted.columns:
        pivoted = pivoted.rename(columns={'T2': 'TONG_T2'})
    else:
        pivoted['TONG_T2'] = 0
    
    pivoted['TONG_DELTA'] = pivoted['TONG_T2'] - pivoted['TONG_T1']
    
    return pivoted[['DP_GROUP', 'TONG_T1', 'TONG_T2', 'TONG_DELTA']].sort_values('TONG_DELTA', ascending=False)


def summary_by_change_type(comparison_df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate summary by change type (MO_MOI, TAT_TOAN, TANG, GIAM, KHONG_DOI).
    
    Args:
        comparison_df: Comparison DataFrame
        
    Returns:
        Summary by change type
    """
    if comparison_df.empty:
        return pd.DataFrame()
    
    grouped = comparison_df.groupby('BIEN_DONG', as_index=False).agg({
        'MA_KH': 'count',
        'DELTA': ['sum', 'mean'],
        'TOTAL_T1': 'sum',
        'TOTAL_T2': 'sum'
    }).rename(columns={'MA_KH': 'SO_KH'})
    
    # Flatten column names
    grouped.columns = ['BIEN_DONG', 'SO_KH', 'TONG_DELTA', 'DELTA_TRUNG_BINH', 'TONG_T1', 'TONG_T2']
    
    return grouped[['BIEN_DONG', 'SO_KH', 'TONG_DELTA', 'DELTA_TRUNG_BINH']].sort_values('SO_KH', ascending=False)


def get_pivot_for_branch_chart(summary_branch: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare data for branch growth chart.
    
    Args:
        summary_branch: Summary by branch
        
    Returns:
        Formatted data for chart
    """
    if summary_branch.empty:
        return pd.DataFrame()
    
    # Return sorted by delta for better visualization
    return summary_branch.sort_values('TONG_DELTA', ascending=False)
