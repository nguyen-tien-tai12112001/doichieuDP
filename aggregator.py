"""
Aggregation module for grouping and calculating totals.
"""
from typing import Dict
import pandas as pd


def group_by_customer(df: pd.DataFrame, include_branch: bool = False) -> pd.DataFrame:
    """
    Group data by customer and sum balances.
    
    Args:
        df: Input DataFrame
        include_branch: If True, include MA_CN in grouping
        
    Returns:
        Aggregated DataFrame with TOTAL_BALANCE
    """
    if df.empty:
        return pd.DataFrame()
    
    group_cols = ['MA_KH', 'TEN_KH', 'CUST_TYPE_NAME']
    if include_branch and '_branch' in df.columns:
        group_cols = ['_branch'] + group_cols
    
    agg_df = df.groupby(group_cols, as_index=False).agg({
        'CURRENT_BALANCE': 'sum'
    }).rename(columns={'CURRENT_BALANCE': 'TOTAL_BALANCE'})
    
    return agg_df


def aggregate_pair(df_t1: pd.DataFrame, df_t2: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate T1 and T2 data by customer.
    
    Args:
        df_t1: T1 data (already filtered)
        df_t2: T2 data (already filtered)
        
    Returns:
        DataFrame with aggregated balances for both periods
    """
    agg_t1 = group_by_customer(df_t1, include_branch=True)
    agg_t2 = group_by_customer(df_t2, include_branch=True)
    
    # Rename columns for clarity
    agg_t1 = agg_t1.rename(columns={'TOTAL_BALANCE': 'TOTAL_T1'})
    agg_t2 = agg_t2.rename(columns={'TOTAL_BALANCE': 'TOTAL_T2'})
    
    return agg_t1, agg_t2


def group_by_branch(df: pd.DataFrame) -> pd.DataFrame:
    """
    Group aggregated data by branch (MA_CN).
    
    Args:
        df: DataFrame with TOTAL_T1, TOTAL_T2, DELTA columns
        
    Returns:
        DataFrame grouped by MA_CN
    """
    if df.empty:
        return pd.DataFrame()
    
    grouped = df.groupby('MA_CN', as_index=False).agg({
        'TOTAL_T1': 'sum',
        'TOTAL_T2': 'sum',
        'DELTA': 'sum',
        'MA_KH': 'count'  # Count unique customers
    }).rename(columns={'MA_KH': 'SO_KH'})
    
    # Calculate growth rate
    grouped['TY_LE_TANG_TRUONG'] = grouped.apply(
        lambda row: (row['TONG_DELTA'] / row['TONG_T1']) if row['TONG_T1'] != 0 else 0,
        axis=1
    )
    
    # Rename for consistency
    grouped = grouped.rename(columns={
        'TOTAL_T1': 'TONG_T1',
        'TOTAL_T2': 'TONG_T2',
        'DELTA': 'TONG_DELTA'
    })
    
    return grouped[['MA_CN', 'TONG_T1', 'TONG_T2', 'TONG_DELTA', 'SO_KH', 'TY_LE_TANG_TRUONG']]


def group_by_customer_type(df: pd.DataFrame) -> pd.DataFrame:
    """
    Group by customer type (CUST_TYPE_NAME).
    
    Args:
        df: DataFrame with comparison data
        
    Returns:
        Aggregated by customer type
    """
    if df.empty:
        return pd.DataFrame()
    
    grouped = df.groupby('CUST_TYPE_NAME', as_index=False).agg({
        'TOTAL_T1': 'sum',
        'TOTAL_T2': 'sum',
        'DELTA': 'sum'
    }).rename(columns={
        'TOTAL_T1': 'TONG_T1',
        'TOTAL_T2': 'TONG_T2',
        'DELTA': 'TONG_DELTA'
    })
    
    return grouped[['CUST_TYPE_NAME', 'TONG_T1', 'TONG_T2', 'TONG_DELTA']]


def group_by_product_group(df: pd.DataFrame, dp_mapping: Dict[str, str]) -> pd.DataFrame:
    """
    Group by product type group.
    
    Args:
        df: DataFrame with original DP_TYPE_CODE data
        dp_mapping: Dict mapping DP_TYPE_CODE to DP_GROUP
        
    Returns:
        Aggregated by product group
    """
    if df.empty:
        return pd.DataFrame()
    
    # Map DP_TYPE_CODE to group
    if 'DP_TYPE_CODE' in df.columns:
        df = df.copy()
        df['DP_GROUP'] = df['DP_TYPE_CODE'].map(dp_mapping).fillna('OTHER')
        
        grouped = df.groupby('DP_GROUP', as_index=False).agg({
            'CURRENT_BALANCE': 'sum'
        }).rename(columns={'CURRENT_BALANCE': 'TOTAL_BALANCE'})
        
        return grouped[['DP_GROUP', 'TOTAL_BALANCE']]
    
    return pd.DataFrame()
