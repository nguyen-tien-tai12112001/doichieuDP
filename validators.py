"""Validators module for file and data validation."""

import os
import re
from typing import Dict, List, Optional, Tuple

import pandas as pd


REQUIRED_COLUMNS = ['MA_KH', 'TEN_KH', 'DP_TYPE_CODE', 'CURRENT_BALANCE', 'CUST_TYPE_NAME']
FILE_PATTERN = r'^(\d{4})_dp01_(\d{8})\.csv$'


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


def validate_filename(filename: str) -> Tuple[str, str]:
    """
    Validate filename format and extract MA_CN and date.
    
    Args:
        filename: File name to validate
        
    Returns:
        Tuple of (MA_CN, yyyymmdd)
        
    Raises:
        ValidationError: If filename doesn't match pattern
    """
    match = re.match(FILE_PATTERN, filename)
    if not match:
        raise ValidationError(
            f"Tên file '{filename}' không hợp lệ. "
            f"Định dạng cần: {{MA_CN}}_dp01_yyyymmdd.csv"
        )
    return match.group(1), match.group(2)


def validate_files_date_consistency(files: List[str], location: str) -> str:
    """
    Check all files have same yyyymmdd.
    
    Args:
        files: List of filenames
        location: T1 or T2 for error message
        
    Returns:
        The yyyymmdd if all consistent
        
    Raises:
        ValidationError: If dates are inconsistent
    """
    if not files:
        raise ValidationError(f"Không có file nào trong {location}")
    
    dates = set()
    for filename in files:
        _, date = validate_filename(filename)
        dates.add(date)
    
    if len(dates) > 1:
        raise ValidationError(
            f"Tất cả file trong {location} phải có cùng ngày yyyymmdd. "
            f"Tìm thấy: {', '.join(sorted(dates))}"
        )
    
    return dates.pop()


def validate_branch_codes_match(t1_files: List[str], t2_files: List[str]) -> Dict[str, str]:
    """
    Check if MA_CN (branch codes) match between T1 and T2.
    
    Args:
        t1_files: List of T1 filenames
        t2_files: List of T2 filenames
        
    Returns:
        Dict mapping MA_CN to (T1_date, T2_date)
        
    Raises:
        ValidationError: If branch codes don't match
    """
    t1_branches = {}
    t2_branches = {}
    
    for filename in t1_files:
        ma_cn, date = validate_filename(filename)
        t1_branches[ma_cn] = date
    
    for filename in t2_files:
        ma_cn, date = validate_filename(filename)
        t2_branches[ma_cn] = date
    
    t1_set = set(t1_branches.keys())
    t2_set = set(t2_branches.keys())
    
    if t1_set != t2_set:
        missing_in_t2 = t1_set - t2_set
        missing_in_t1 = t2_set - t1_set
        error_msg = "Các mã chi nhánh không khớp giữa T1 và T2:\n"
        if missing_in_t2:
            error_msg += f"• Thiếu trong T2: {', '.join(sorted(missing_in_t2))}\n"
        if missing_in_t1:
            error_msg += f"• Thiếu trong T1: {', '.join(sorted(missing_in_t1))}"
        raise ValidationError(error_msg)
    
    # Create mapping (MA_CN -> (T1_date, T2_date))
    branch_dates = {}
    for ma_cn in t1_set:
        branch_dates[ma_cn] = (t1_branches[ma_cn], t2_branches[ma_cn])
    
    return branch_dates


def validate_csv_headers(filepath: str, column_mapping: Optional[Dict[str, str]] = None) -> None:
    """
    Validate that CSV has all required columns.
    
    Args:
        filepath: Path to CSV file
        
    Raises:
        ValidationError: If required columns are missing
    """
    try:
        df = pd.read_csv(filepath, nrows=0)
        mapping = column_mapping or {col: col for col in REQUIRED_COLUMNS}
        expected_source_cols = {mapping.get(col, col) for col in REQUIRED_COLUMNS}
        missing_cols = expected_source_cols - set(df.columns)
        
        if missing_cols:
            raise ValidationError(
                f"File '{os.path.basename(filepath)}' thiếu cột: "
                f"{', '.join(sorted(missing_cols))}"
            )
    except pd.errors.ParserError as e:
        raise ValidationError(f"Lỗi đọc file '{os.path.basename(filepath)}': {str(e)}")
    except Exception as e:
        raise ValidationError(f"Lỗi validating file '{os.path.basename(filepath)}': {str(e)}")


def validate_all_files(
    t1_files: List[str],
    t2_files: List[str],
    column_mapping: Optional[Dict[str, str]] = None,
) -> Dict[str, str]:
    """
    Run all validations on uploaded files.
    
    Args:
        t1_files: List of T1 file paths
        t2_files: List of T2 file paths
        
    Returns:
        Dict with validation results
        
    Raises:
        ValidationError: If any validation fails
    """
    # Extract just filenames
    t1_filenames = [os.path.basename(f) for f in t1_files]
    t2_filenames = [os.path.basename(f) for f in t2_files]
    
    # Validate date consistency within T1 and T2
    t1_date = validate_files_date_consistency(t1_filenames, "T1")
    t2_date = validate_files_date_consistency(t2_filenames, "T2")
    
    # Validate branch codes match
    branch_dates = validate_branch_codes_match(t1_filenames, t2_filenames)
    
    # Validate CSV headers
    for filepath in t1_files + t2_files:
        validate_csv_headers(filepath, column_mapping=column_mapping)
    
    return {
        "t1_date": t1_date,
        "t2_date": t2_date,
        "branch_dates": branch_dates,
        "valid": True
    }
