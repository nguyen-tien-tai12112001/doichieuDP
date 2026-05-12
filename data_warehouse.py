"""
Data Warehouse module for managing deposit data files.
Provides functions to import, store, list, and delete files from a centralized warehouse.
"""

import os
import sqlite3
import hashlib
import shutil
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import pandas as pd
import re
from contextlib import contextmanager

DATABASE_FILE = Path('app_database.db')
WAREHOUSE_DIR = Path('data_warehouse')

# Ensure warehouse directory exists
WAREHOUSE_DIR.mkdir(exist_ok=True)


@contextmanager
def get_db_connection():
    """Context manager for database connections."""
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_warehouse_tables():
    """Initialize warehouse-related database tables if they don't exist."""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Warehouse files table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS warehouse_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_name TEXT NOT NULL,
                stored_name TEXT NOT NULL UNIQUE,
                file_hash TEXT NOT NULL,
                file_path TEXT NOT NULL,
                branch_code TEXT,
                record_count INTEGER,
                total_balance REAL,
                min_balance REAL,
                max_balance REAL,
                avg_balance REAL,
                data_date TEXT,
                import_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                file_size INTEGER,
                validation_status TEXT DEFAULT 'pending'
            )
        ''')
        
        # File tags table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS file_tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id INTEGER NOT NULL,
                tag TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (file_id) REFERENCES warehouse_files(id),
                UNIQUE(file_id, tag)
            )
        ''')
        
        # File versions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS file_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id INTEGER NOT NULL,
                version_number INTEGER,
                stored_name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                record_count INTEGER,
                total_balance REAL,
                FOREIGN KEY (file_id) REFERENCES warehouse_files(id)
            )
        ''')
        
        # Add missing columns (migration)
        cursor.execute("PRAGMA table_info(warehouse_files)")
        existing_columns = [row[1] for row in cursor.fetchall()]
        
        if 'min_balance' not in existing_columns:
            cursor.execute('ALTER TABLE warehouse_files ADD COLUMN min_balance REAL')
        
        if 'max_balance' not in existing_columns:
            cursor.execute('ALTER TABLE warehouse_files ADD COLUMN max_balance REAL')
        
        if 'avg_balance' not in existing_columns:
            cursor.execute('ALTER TABLE warehouse_files ADD COLUMN avg_balance REAL')
        
        if 'validation_status' not in existing_columns:
            cursor.execute("ALTER TABLE warehouse_files ADD COLUMN validation_status TEXT DEFAULT 'pending'")

        if 'data_date' not in existing_columns:
            cursor.execute('ALTER TABLE warehouse_files ADD COLUMN data_date TEXT')

        cursor.execute('SELECT id, original_name FROM warehouse_files WHERE data_date IS NULL OR data_date = ""')
        rows_to_backfill = cursor.fetchall()
        for row in rows_to_backfill:
            data_date = extract_data_date(row['original_name'])
            if data_date:
                cursor.execute(
                    'UPDATE warehouse_files SET data_date = ? WHERE id = ?',
                    (data_date, row['id'])
                )

        conn.commit()


def extract_data_date(filename: str) -> Optional[str]:
    """
    Extract business data date from filename.
    Expected format: {MA_CN}_dp01_yyyymmdd.csv
    Returns ISO date string yyyy-mm-dd for UI/database filtering.
    """
    match = re.match(r'^\d{4}_dp01_(\d{8})\.csv$', filename)
    if not match:
        return None

    raw_date = match.group(1)
    try:
        return datetime.strptime(raw_date, '%Y%m%d').date().isoformat()
    except ValueError:
        return None


def extract_branch_code(filename: str) -> Optional[str]:
    """
    Extract branch code (MA_CN) from filename.
    Expected format: {MA_CN}_dp01_yyyymmdd.csv
    """
    match = re.match(r'^(\d{4})_dp01_\d{8}\.csv$', filename)
    return match.group(1) if match else None


def calculate_file_hash(filepath: str) -> str:
    """Calculate SHA256 hash of file content."""
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            sha256.update(chunk)
    return sha256.hexdigest()


def import_file_to_warehouse(filepath: str) -> Tuple[int, str]:
    """
    Import a single CSV file into the warehouse.
    
    Args:
        filepath: Path to the CSV file to import
        
    Returns:
        Tuple of (file_id, status_message)
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")

    original_name = os.path.basename(filepath)
    print(f"DEBUG: Processing file: {original_name}")
    
    branch_code = extract_branch_code(original_name)
    data_date = extract_data_date(original_name)
    
    print(f"DEBUG: Extracted branch_code: {branch_code}, data_date: {data_date}")
    
    if not branch_code or not data_date:
        raise ValueError(f"Invalid filename format: {original_name}. Expected: {{MA_CN}}_dp01_yyyymmdd.csv")

    # Check if same file name already exists in warehouse
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM warehouse_files WHERE original_name = ?', (original_name,))
        existing_name = cursor.fetchone()
        if existing_name:
            print(f"DEBUG: File with same name already exists: {original_name} (ID: {existing_name['id']})")
            return existing_name['id'], f"File with same name already imported (ID: {existing_name['id']})"

    # Calculate file hash for deduplication
    file_hash = calculate_file_hash(filepath)
    print(f"DEBUG: File hash: {file_hash}")
    
    # Check if file already exists in warehouse by content
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM warehouse_files WHERE file_hash = ?', (file_hash,))
        existing = cursor.fetchone()
        
        if existing:
            print(f"DEBUG: File already exists with ID: {existing['id']}")
            return existing['id'], f"File already exists in warehouse (ID: {existing['id']})"

    # Read file to get statistics
    try:
        print(f"DEBUG: Reading CSV file: {filepath}")
        df = pd.read_csv(filepath)
        record_count = len(df)
        print(f"DEBUG: File has {record_count} records")
        
        # Calculate balance statistics
        if 'CURRENT_BALANCE' in df.columns:
            balance_series = pd.to_numeric(df['CURRENT_BALANCE'], errors='coerce').dropna()
            total_balance = balance_series.sum()
            min_balance = balance_series.min() if len(balance_series) > 0 else None
            max_balance = balance_series.max() if len(balance_series) > 0 else None
            avg_balance = balance_series.mean() if len(balance_series) > 0 else None
            print(f"DEBUG: Balance stats - total: {total_balance}, count: {len(balance_series)}")
        else:
            total_balance = 0
            min_balance = None
            max_balance = None
            avg_balance = None
            print("DEBUG: No CURRENT_BALANCE column found")
    except Exception as e:
        print(f"DEBUG: Error reading file: {str(e)}")
        raise ValueError(f"Error reading file {original_name}: {str(e)}")

    # Generate unique stored name
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    file_ext = os.path.splitext(original_name)[1]
    stored_name = f"{timestamp}_{hashlib.md5(original_name.encode()).hexdigest()[:8]}{file_ext}"
    
    # Copy file to warehouse
    warehouse_path = WAREHOUSE_DIR / stored_name
    shutil.copy2(filepath, warehouse_path)
    
    file_size = os.path.getsize(warehouse_path)
    print(f"DEBUG: File copied to: {warehouse_path}, size: {file_size}")

    # Record in database
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO warehouse_files 
            (original_name, stored_name, file_hash, file_path, branch_code, data_date, record_count, total_balance, min_balance, max_balance, avg_balance, file_size)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            original_name,
            stored_name,
            file_hash,
            str(warehouse_path),
            branch_code,
            data_date,
            record_count,
            total_balance,
            min_balance,
            max_balance,
            avg_balance,
            file_size,
        ))
        
        file_id = cursor.lastrowid
        conn.commit()
        print(f"DEBUG: File imported successfully with ID: {file_id}")

    return file_id, f"File imported successfully (ID: {file_id})"


def import_files_batch(file_paths: List[str]) -> Dict[str, any]:
    """
    Import multiple files to warehouse at once.
    
    Args:
        file_paths: List of file paths to import
        
    Returns:
        Dictionary with results
    """
    results = {
        'imported': [],
        'duplicates': [],
        'errors': [],
    }
    
    for filepath in file_paths:
        try:
            file_id, message = import_file_to_warehouse(filepath)
            if 'already exists' in message:
                results['duplicates'].append({'file': os.path.basename(filepath), 'id': file_id})
            else:
                results['imported'].append({'file': os.path.basename(filepath), 'id': file_id})
        except Exception as e:
            results['errors'].append({'file': os.path.basename(filepath), 'error': str(e)})
    
    return results


def list_warehouse_files() -> pd.DataFrame:
    """
    List all files in the warehouse.
    
    Returns:
        DataFrame with file information
    """
    with get_db_connection() as conn:
        query = '''
            SELECT 
                id,
                original_name,
                branch_code,
                data_date,
                record_count,
                total_balance,
                min_balance,
                max_balance,
                avg_balance,
                import_date,
                file_size,
                validation_status
            FROM warehouse_files
            ORDER BY data_date DESC, import_date DESC
        '''
        df = pd.read_sql(query, conn)
        if 'import_date' in df.columns:
            df['import_date'] = pd.to_datetime(df['import_date'], errors='coerce')
        if 'data_date' in df.columns:
            df['data_date'] = pd.to_datetime(df['data_date'], errors='coerce')
        return df


def get_warehouse_files_by_branch(branch_code: str) -> pd.DataFrame:
    """
    Get all warehouse files for a specific branch.
    
    Args:
        branch_code: Branch code (MA_CN)
        
    Returns:
        DataFrame with files for that branch
    """
    with get_db_connection() as conn:
        query = '''
            SELECT 
                id,
                original_name,
                branch_code,
                data_date,
                record_count,
                total_balance,
                min_balance,
                max_balance,
                avg_balance,
                import_date,
                file_size,
                validation_status
            FROM warehouse_files
            WHERE branch_code = ?
            ORDER BY data_date DESC, import_date DESC
        '''
        return pd.read_sql(query, conn, params=(branch_code,))


def get_file_path(file_id: int) -> Optional[str]:
    """
    Get the full file path for a warehouse file.
    
    Args:
        file_id: ID of the file in warehouse
        
    Returns:
        File path or None if not found
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT file_path FROM warehouse_files WHERE id = ?', (file_id,))
        row = cursor.fetchone()
    
    if row and row['file_path'] and os.path.exists(row['file_path']):
        return row['file_path']
    return None


def get_file_info(file_id: int) -> Optional[Dict]:
    """
    Get detailed information about a warehouse file.
    
    Args:
        file_id: ID of the file in warehouse
        
    Returns:
        Dictionary with file information or None
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM warehouse_files WHERE id = ?
        ''', (file_id,))
        row = cursor.fetchone()
    
    if row:
        return dict(row)
    return None


def delete_warehouse_file(file_id: int) -> str:
    """
    Delete a file from the warehouse.
    
    Args:
        file_id: ID of the file to delete
        
    Returns:
        Status message
    """
    file_info = get_file_info(file_id)
    if not file_info:
        raise ValueError(f"File not found: {file_id}")

    # Delete physical file
    if file_info['file_path'] and os.path.exists(file_info['file_path']):
        try:
            os.remove(file_info['file_path'])
        except Exception as e:
            raise Exception(f"Error deleting file: {str(e)}")

    # Delete database record
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM warehouse_files WHERE id = ?', (file_id,))
        conn.commit()

    return f"File {file_info['original_name']} deleted successfully"


def delete_warehouse_files_batch(file_ids: List[int]) -> Dict[str, any]:
    """
    Delete multiple files from warehouse at once.
    
    Args:
        file_ids: List of file IDs to delete
        
    Returns:
        Dictionary with results
    """
    results = {
        'deleted': [],
        'errors': [],
    }
    
    for file_id in file_ids:
        try:
            message = delete_warehouse_file(file_id)
            results['deleted'].append({'id': file_id, 'message': message})
        except Exception as e:
            results['errors'].append({'id': file_id, 'error': str(e)})
    
    return results


def get_warehouse_stats() -> Dict:
    """
    Get statistics about the warehouse.
    
    Returns:
        Dictionary with warehouse statistics
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Total files
        cursor.execute('SELECT COUNT(*) as count FROM warehouse_files')
        total_files = cursor.fetchone()['count']
        
        # Total size
        cursor.execute('SELECT SUM(file_size) as total FROM warehouse_files')
        total_size = cursor.fetchone()['total'] or 0
        
        # Unique branches
        cursor.execute('SELECT COUNT(DISTINCT branch_code) as count FROM warehouse_files')
        total_branches = cursor.fetchone()['count']
        
        # Total records
        cursor.execute('SELECT SUM(record_count) as total FROM warehouse_files')
        total_records = cursor.fetchone()['total'] or 0
        
        # Total balance
        cursor.execute('SELECT SUM(total_balance) as total FROM warehouse_files')
        total_balance = cursor.fetchone()['total'] or 0

    return {
        'total_files': total_files,
        'total_size': total_size,
        'total_branches': total_branches,
        'total_records': total_records,
        'total_balance': total_balance,
    }


def validate_file_selection(file_ids: List[int]) -> Tuple[bool, str]:
    """
    Validate a selection of files for comparison.
    
    Conditions:
    - All files must exist
    - All files must have different branches OR same number of branches
    
    Args:
        file_ids: List of file IDs to validate
        
    Returns:
        Tuple of (is_valid, message)
    """
    if not file_ids or len(set(file_ids)) < 2:
        return False, "Need at least 2 files to compare"

    files_info = []
    for file_id in file_ids:
        info = get_file_info(file_id)
        if not info:
            return False, f"File not found: {file_id}"
        files_info.append(info)

    # Check all files have same structure (same branches for T1 and T2)
    # This will be validated when user selects files for T1 and T2
    return True, "Valid file selection"


# ==================== FILE TAGGING ====================

def add_file_tag(file_id: int, tag: str) -> bool:
    """Add a tag to a file."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT OR IGNORE INTO file_tags (file_id, tag) VALUES (?, ?)', (file_id, tag))
            conn.commit()
        return True
    except Exception:
        return False


def remove_file_tag(file_id: int, tag: str) -> bool:
    """Remove a tag from a file."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM file_tags WHERE file_id = ? AND tag = ?', (file_id, tag))
            conn.commit()
        return True
    except Exception:
        return False


def get_file_tags(file_id: int) -> List[str]:
    """Get all tags for a file."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT tag FROM file_tags WHERE file_id = ? ORDER BY tag', (file_id,))
        return [row['tag'] for row in cursor.fetchall()]


def get_files_by_tag(tag: str) -> pd.DataFrame:
    """Get all files with a specific tag."""
    with get_db_connection() as conn:
        query = '''
            SELECT DISTINCT wf.* FROM warehouse_files wf
            JOIN file_tags ft ON wf.id = ft.file_id
            WHERE ft.tag = ?
            ORDER BY wf.import_date DESC
        '''
        return pd.read_sql(query, conn, params=(tag,))


# ==================== FILE VALIDATION ====================

def update_file_validation_status(file_id: int, status: str, details: str = '') -> bool:
    """Update validation status of a file."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE warehouse_files 
                SET validation_status = ?
                WHERE id = ?
            ''', (status, file_id))
            conn.commit()
        return True
    except Exception:
        return False


def get_validation_status(file_id: int) -> str:
    """Get validation status of a file."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT validation_status FROM warehouse_files WHERE id = ?', (file_id,))
        row = cursor.fetchone()
    return row['validation_status'] if row else 'unknown'


# ==================== FILE VERSIONING ====================

def create_file_version(file_id: int, version_number: int, stored_name: str, record_count: int, total_balance: float) -> bool:
    """Create a new version of a file."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO file_versions (file_id, version_number, stored_name, record_count, total_balance)
                VALUES (?, ?, ?, ?, ?)
            ''', (file_id, version_number, stored_name, record_count, total_balance))
            conn.commit()
        return True
    except Exception:
        return False


def get_file_versions(file_id: int) -> pd.DataFrame:
    """Get all versions of a file."""
    with get_db_connection() as conn:
        query = 'SELECT * FROM file_versions WHERE file_id = ? ORDER BY version_number DESC'
        return pd.read_sql(query, conn, params=(file_id,))


# ==================== AUTO-MATCHING ====================

def find_matching_t2_file(t1_file_id: int, available_files: pd.DataFrame) -> Optional[int]:
    """
    Find the best matching T2 file for a given T1 file.
    Matching criteria:
    1. Same branch code
    2. Import date closest to T1 but not before T1
    3. Recent files preferred
    """
    t1_info = get_file_info(t1_file_id)
    if not t1_info:
        return None
    
    t1_branch = t1_info['branch_code']
    
    # Filter by branch
    matching = available_files[available_files['branch_code'] == t1_branch]
    if matching.empty:
        return None
    
    # Sort by data_date first, then import_date as a tie breaker.
    sort_cols = [col for col in ['data_date', 'import_date'] if col in matching.columns]
    matching = matching.sort_values(sort_cols, ascending=False)
    
    # Return first (most recent)
    return matching.iloc[0]['id']


def suggest_file_pairs(t1_files: List[int], available_files: pd.DataFrame) -> Dict[int, int]:
    """
    Suggest T2 files for each T1 file.
    Returns dictionary {t1_id: t2_id}
    """
    suggestions = {}
    for t1_id in t1_files:
        t2_id = find_matching_t2_file(t1_id, available_files)
        if t2_id and t2_id != t1_id:
            suggestions[t1_id] = t2_id
    return suggestions


# ==================== STATISTICS ====================

def get_file_statistics() -> Dict:
    """Get advanced statistics about warehouse files."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # By branch
        cursor.execute('''
            SELECT branch_code, COUNT(*) as count, SUM(record_count) as total_records
            FROM warehouse_files
            GROUP BY branch_code
            ORDER BY count DESC
        ''')
        by_branch = {row['branch_code']: {'count': row['count'], 'records': row['total_records']} 
                     for row in cursor.fetchall()}
        
        # By business data date
        cursor.execute('''
            SELECT data_date as date, COUNT(*) as count
            FROM warehouse_files
            WHERE data_date IS NOT NULL AND data_date != ''
            GROUP BY data_date
            ORDER BY date DESC
        ''')
        by_date = {row['date']: row['count'] for row in cursor.fetchall()}
        
        # Tags
        cursor.execute('''
            SELECT tag, COUNT(*) as count
            FROM file_tags
            GROUP BY tag
            ORDER BY count DESC
        ''')
        by_tag = {row['tag']: row['count'] for row in cursor.fetchall()}
        
    return {
        'by_branch': by_branch,
        'by_date': by_date,
        'by_tag': by_tag,
    }


# Initialize tables on module load
init_warehouse_tables()
