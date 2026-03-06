"""
Outlier detection engine using IQR and Z-score methods.
"""
import pandas as pd
import numpy as np
from scipy import stats


def detect_outliers_iqr(df: pd.DataFrame, column: str = 'DELTA', iqr_multiplier: float = 1.5) -> pd.DataFrame:
    """
    Detect outliers using Interquartile Range (IQR) method.
    
    Args:
        df: Comparison DataFrame
        column: Column to analyze (default: DELTA)
        iqr_multiplier: IQR multiplier for outlier threshold (default: 1.5)
        
    Returns:
        DataFrame with only outliers
    """
    if df.empty or column not in df.columns:
        return pd.DataFrame()
    
    df = df.copy()
    
    # Calculate Q1, Q3, IQR
    q1 = df[column].quantile(0.25)
    q3 = df[column].quantile(0.75)
    iqr = q3 - q1
    
    # Define outlier boundaries
    lower_bound = q1 - (iqr_multiplier * iqr)
    upper_bound = q3 + (iqr_multiplier * iqr)
    
    # Identify outliers
    df['IS_OUTLIER'] = ((df[column] < lower_bound) | (df[column] > upper_bound))
    df['OUTLIER_METHOD'] = 'IQR'
    df['OUTLIER_THRESHOLD'] = f'{lower_bound:.2f} to {upper_bound:.2f}'
    
    return df[df['IS_OUTLIER']].copy()


def detect_outliers_zscore(df: pd.DataFrame, column: str = 'DELTA', threshold: float = 3.0) -> pd.DataFrame:
    """
    Detect outliers using Z-score method.
    
    Args:
        df: Comparison DataFrame
        column: Column to analyze (default: DELTA)
        threshold: Z-score threshold (default: 3.0 = 99.7% confidence)
        
    Returns:
        DataFrame with only outliers
    """
    if df.empty or column not in df.columns:
        return pd.DataFrame()
    
    df = df.copy()
    
    # Calculate Z-scores
    z_scores = np.abs(stats.zscore(df[column], nan_policy='omit'))
    
    # Identify outliers
    df['IS_OUTLIER'] = z_scores > threshold
    df['Z_SCORE'] = z_scores
    df['OUTLIER_METHOD'] = 'Z-Score'
    df['OUTLIER_THRESHOLD'] = f'> {threshold}'
    
    return df[df['IS_OUTLIER']].copy()


def detect_outliers_combined(df: pd.DataFrame, method: str = 'iqr', **kwargs) -> pd.DataFrame:
    """
    Detect outliers using specified method.
    
    Args:
        df: Comparison DataFrame
        method: 'iqr' or 'zscore'
        **kwargs: Additional parameters for the method
        
    Returns:
        DataFrame with outliers marked and additional info
    """
    if method.lower() == 'iqr':
        return detect_outliers_iqr(df, **kwargs)
    elif method.lower() == 'zscore':
        return detect_outliers_zscore(df, **kwargs)
    else:
        # Default to IQR
        return detect_outliers_iqr(df, **kwargs)


def analyze_outliers(outliers_df: pd.DataFrame) -> dict:
    """
    Generate analysis summary for outliers.
    
    Args:
        outliers_df: DataFrame containing only outliers
        
    Returns:
        Dict with outlier statistics
    """
    if outliers_df.empty:
        return {
            'total_outliers': 0,
            'positive_outliers': 0,
            'negative_outliers': 0,
            'avg_delta': 0,
            'max_delta': 0,
            'min_delta': 0,
            'top_branches': pd.DataFrame(),
            'top_customers': pd.DataFrame()
        }
    
    analysis = {
        'total_outliers': len(outliers_df),
        'positive_outliers': len(outliers_df[outliers_df['DELTA'] > 0]),
        'negative_outliers': len(outliers_df[outliers_df['DELTA'] < 0]),
        'avg_delta': outliers_df['DELTA'].mean(),
        'max_delta': outliers_df['DELTA'].max(),
        'min_delta': outliers_df['DELTA'].min(),
    }
    
    # Top branches by outlier count
    if 'MA_CN' in outliers_df.columns:
        analysis['top_branches'] = outliers_df.groupby('MA_CN').agg({
            'MA_KH': 'count',
            'DELTA': ['sum', 'mean']
        }).rename(columns={'MA_KH': 'SO_KH'}).sort_values(('DELTA', 'sum'), ascending=False).head(10)
    
    # Top customers by delta magnitude
    analysis['top_customers'] = outliers_df[[
        'MA_CN', 'MA_KH', 'TEN_KH', 'CUST_TYPE_NAME', 'TOTAL_T1', 'TOTAL_T2', 'DELTA', 'BIEN_DONG'
    ]].copy()
    analysis['top_customers']['ABS_DELTA'] = analysis['top_customers']['DELTA'].abs()
    analysis['top_customers'] = analysis['top_customers'].sort_values('ABS_DELTA', ascending=False).head(20)
    
    return analysis


def get_outliers_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Get summary of outliers with key information.
    
    Args:
        df: Comparison DataFrame
        
    Returns:
        DataFrame with outlier summary
    """
    outliers = detect_outliers_iqr(df)
    
    if outliers.empty:
        return pd.DataFrame()
    
    # Sort by absolute delta
    outliers['ABS_DELTA'] = outliers['DELTA'].abs()
    outliers = outliers.sort_values('ABS_DELTA', ascending=False)
    
    # Select important columns
    cols = ['MA_CN', 'MA_KH', 'TEN_KH', 'CUST_TYPE_NAME', 'TOTAL_T1', 'TOTAL_T2', 'DELTA', 'BIEN_DONG']
    return outliers[[col for col in cols if col in outliers.columns]].head(50)
