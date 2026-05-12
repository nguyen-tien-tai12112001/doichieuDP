"""Data loader module for reading and normalizing CSV files."""

import os
from typing import Dict, Optional

import pandas as pd


CANONICAL_COLUMNS = ['MA_KH', 'TEN_KH', 'DP_TYPE_CODE', 'CURRENT_BALANCE', 'CUST_TYPE_NAME']
LARGE_FILE_THRESHOLD_BYTES = 20 * 1024 * 1024  # 20MB threshold for chunked reading
DEFAULT_CHUNK_SIZE = 200_000


def _build_rename_map(column_mapping: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """Build source->canonical rename map from canonical->source mapping."""
    mapping = column_mapping or {col: col for col in CANONICAL_COLUMNS}
    rename_map = {}

    for canonical in CANONICAL_COLUMNS:
        source = mapping.get(canonical, canonical)
        if source != canonical:
            rename_map[source] = canonical

    return rename_map


def _read_csv_safely(filepath: str) -> pd.DataFrame:
    """Read CSV in normal mode or chunked mode for large files."""
    file_size = os.path.getsize(filepath)

    if file_size < LARGE_FILE_THRESHOLD_BYTES:
        return pd.read_csv(filepath)
    else:
        # For large files, use chunked reading
        chunks = []
        for chunk in pd.read_csv(filepath, chunksize=DEFAULT_CHUNK_SIZE):
            chunks.append(chunk)
        return pd.concat(chunks, ignore_index=True) if chunks else pd.DataFrame()


def load_and_normalize_csv(filepath: str, column_mapping: Optional[Dict[str, str]] = None) -> pd.DataFrame:
    """
    Load CSV and normalize data types.
    
    Args:
        filepath: Path to CSV file
        
    Returns:
        DataFrame with normalized columns
    """
    df = _read_csv_safely(filepath)

    rename_map = _build_rename_map(column_mapping)
    if rename_map:
        df = df.rename(columns=rename_map)
    
    # Normalize data types
    df['MA_KH'] = df['MA_KH'].astype(str).str.strip()
    df['TEN_KH'] = df['TEN_KH'].astype(str).str.strip()
    df['DP_TYPE_CODE'] = df['DP_TYPE_CODE'].astype(str).str.strip()
    df['CURRENT_BALANCE'] = pd.to_numeric(df['CURRENT_BALANCE'], errors='coerce').fillna(0)
    df['CUST_TYPE_NAME'] = df['CUST_TYPE_NAME'].astype(str).str.strip()
        
    return df


def load_branch_data(
    ma_cn: str,
    t1_file: str,
    t2_file: str,
    column_mapping: Optional[Dict[str, str]] = None,
) -> Dict[str, pd.DataFrame]:
    """
    Load data for a specific branch from T1 and T2 files.
    
    Args:
        ma_cn: Branch code
        t1_file: Path to T1 CSV
        t2_file: Path to T2 CSV
        
    Returns:
        Dict with 'T1' and 'T2' DataFrames
    """
    # Load both files
    df_t1 = load_and_normalize_csv(t1_file, column_mapping=column_mapping)
    df_t2 = load_and_normalize_csv(t2_file, column_mapping=column_mapping)
    
    # Add metadata
    df_t1['_branch'] = ma_cn
    df_t2['_branch'] = ma_cn
    df_t1['_period'] = 'T1'
    df_t2['_period'] = 'T2'
    
    return {'T1': df_t1, 'T2': df_t2}


def filter_valid_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Remove rows with DP_TYPE_CODE in ["401", "101"].
    
    Args:
        df: Input DataFrame
        
    Returns:
        Filtered DataFrame
    """
    exclude_types = ["401", "101"]
    return df[~df['DP_TYPE_CODE'].isin(exclude_types)].copy()


def load_all_branches(
    file_mapping: Dict[str, tuple],
    column_mapping: Optional[Dict[str, str]] = None,
) -> Dict[str, Dict[str, pd.DataFrame]]:
    """
    Load data for all branches.
    
    Args:
        file_mapping: Dict {MA_CN: (T1_file_path, T2_file_path)}
        
    Returns:
        Dict {MA_CN: {'T1': df, 'T2': df}}
    """
    result = {}
    
    for ma_cn, (t1_file, t2_file) in file_mapping.items():
        result[ma_cn] = load_branch_data(ma_cn, t1_file, t2_file, column_mapping=column_mapping)
    
    return result
