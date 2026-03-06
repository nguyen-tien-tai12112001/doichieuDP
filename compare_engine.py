"""
Comparison engine for merging T1 and T2 data and calculating changes.
"""
from typing import List
import pandas as pd


def classify_change(row: pd.Series) -> str:
    """
    Classify the type of change based on T1, T2 values.
    
    Args:
        row: Series with 'TOTAL_T1', 'TOTAL_T2', 'DELTA' columns
        
    Returns:
        Change classification string
    """
    t1 = row['TOTAL_T1']
    t2 = row['TOTAL_T2']
    delta = row['DELTA']
    
    if t1 == 0 and t2 > 0:
        return 'MO_MOI'
    elif t1 > 0 and t2 == 0:
        return 'TAT_TOAN'
    elif delta > 0:
        return 'TANG'
    elif delta < 0:
        return 'GIAM'
    else:
        return 'KHONG_DOI'


def merge_and_compare(agg_t1: pd.DataFrame, agg_t2: pd.DataFrame, ma_cn: str) -> pd.DataFrame:
    """
    Merge T1 and T2 aggregated data and calculate changes.
    
    Args:
        agg_t1: Aggregated T1 data
        agg_t2: Aggregated T2 data
        ma_cn: Branch code
        
    Returns:
        Merged DataFrame with DELTA and BIEN_DONG columns
    """
    # Merge on customer info
    merge_cols = ['MA_KH', 'TEN_KH', 'CUST_TYPE_NAME']
    
    merged = pd.merge(
        agg_t1[merge_cols + ['TOTAL_T1']],
        agg_t2[merge_cols + ['TOTAL_T2']],
        on=merge_cols,
        how='outer'
    )
    
    # Fill NaN with 0
    merged['TOTAL_T1'] = merged['TOTAL_T1'].fillna(0)
    merged['TOTAL_T2'] = merged['TOTAL_T2'].fillna(0)
    
    # Calculate delta
    merged['DELTA'] = merged['TOTAL_T2'] - merged['TOTAL_T1']
    
    # Classify changes
    merged['BIEN_DONG'] = merged.apply(classify_change, axis=1)
    
    # Add branch code at the beginning
    merged.insert(0, 'MA_CN', ma_cn)
    
    # Ensure proper column order
    merged = merged[[
        'MA_CN', 'MA_KH', 'TEN_KH', 'CUST_TYPE_NAME',
        'TOTAL_T1', 'TOTAL_T2', 'DELTA', 'BIEN_DONG'
    ]]
    
    return merged


def process_all_branches(all_branches_agg: dict, ma_cn_list: List[str]) -> pd.DataFrame:
    """
    Process comparison for all branches and combine results.
    
    Args:
        all_branches_agg: Dict {MA_CN: {'T1': agg_df, 'T2': agg_df}}
        ma_cn_list: List of MA_CN to process
        
    Returns:
        Combined DataFrame with all branches
    """
    results = []
    
    for ma_cn in ma_cn_list:
        if ma_cn in all_branches_agg:
            agg_t1 = all_branches_agg[ma_cn]['T1']
            agg_t2 = all_branches_agg[ma_cn]['T2']
            
            comparison = merge_and_compare(agg_t1, agg_t2, ma_cn)
            results.append(comparison)
    
    if results:
        return pd.concat(results, ignore_index=True)
    else:
        return pd.DataFrame()


def get_statistics_by_change_type(df: pd.DataFrame) -> pd.DataFrame:
    """
    Get statistics by change type (BIEN_DONG).
    
    Args:
        df: Comparison DataFrame
        
    Returns:
        Statistics by change type
    """
    if df.empty:
        return pd.DataFrame()
    
    stats = df.groupby('BIEN_DONG', as_index=False).agg({
        'MA_KH': 'count',
        'DELTA': 'sum'
    }).rename(columns={'MA_KH': 'SO_KH'})
    
    return stats[['BIEN_DONG', 'SO_KH', 'DELTA']]
