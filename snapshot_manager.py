"""
Snapshot management module for the deposit comparison system.
Handles creation, storage, retrieval, and comparison of data snapshots.
"""

import os
import sqlite3
import hashlib
import re
import shutil
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import pandas as pd
from contextlib import contextmanager

DATABASE_FILE = Path('app_database.db')
SNAPSHOTS_STORAGE_DIR = Path('snapshots_data')

# Ensure snapshots storage directory exists
SNAPSHOTS_STORAGE_DIR.mkdir(exist_ok=True)


@contextmanager
def get_db_connection():
    """Context manager for database connections."""
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_snapshot_tables():
    """Initialize snapshot-related database tables if they don't exist."""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Snapshots table - stores metadata about each snapshot
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                branch_count INTEGER,
                file_count INTEGER,
                total_records INTEGER,
                total_balance REAL,
                hash_metadata TEXT UNIQUE
            )
        ''')

        # Snapshot files table - stores file metadata and paths for each snapshot
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS snapshot_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                snapshot_id INTEGER NOT NULL,
                file_name TEXT NOT NULL,
                file_hash TEXT,
                file_path TEXT,
                branch_code TEXT,
                record_count INTEGER,
                branch_total REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (snapshot_id) REFERENCES snapshots(id) ON DELETE CASCADE
            )
        ''')

        conn.commit()


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


def calculate_metadata_hash(files_metadata: List[Dict]) -> str:
    """Calculate hash of files metadata for deduplication."""
    import json
    payload = json.dumps(files_metadata, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()


def create_snapshot(
    snapshot_name: str,
    file_paths: List[str],
    description: str = "",
) -> Tuple[int, str]:
    """
    Create a new snapshot by storing files and metadata in persistent storage.
    
    Args:
        snapshot_name: Human-readable name for the snapshot
        file_paths: List of file paths to include in snapshot
        description: Optional description of the snapshot
        
    Returns:
        Tuple of (snapshot_id, status_message)
    """
    if not file_paths:
        raise ValueError("No files provided for snapshot creation")

    # Create snapshot directory
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    snapshot_dir = SNAPSHOTS_STORAGE_DIR / f"{timestamp}_{hashlib.md5(snapshot_name.encode()).hexdigest()[:8]}"
    snapshot_dir.mkdir(exist_ok=True)

    # Prepare file metadata
    files_metadata = []
    branch_codes = set()
    total_records = 0
    total_balance = 0

    for filepath in file_paths:
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")

        filename = os.path.basename(filepath)
        branch_code = extract_branch_code(filename)
        
        if not branch_code:
            raise ValueError(f"Invalid filename format: {filename}. Expected: {{MA_CN}}_dp01_yyyymmdd.csv")

        file_hash = calculate_file_hash(filepath)
        
        # Copy file to snapshot directory
        snapshot_file_path = snapshot_dir / filename
        shutil.copy2(filepath, snapshot_file_path)
        
        # Read file to get statistics
        try:
            df = pd.read_csv(filepath)
            record_count = len(df)
            branch_total = df.get('CURRENT_BALANCE', pd.Series()).sum() if 'CURRENT_BALANCE' in df.columns else 0
        except Exception as e:
            raise ValueError(f"Error reading file {filename}: {str(e)}")

        files_metadata.append({
            'file_name': filename,
            'file_hash': file_hash,
            'file_path': str(snapshot_file_path),
            'branch_code': branch_code,
            'record_count': int(record_count),
            'branch_total': float(branch_total),
        })

        branch_codes.add(branch_code)
        total_records += record_count
        total_balance += branch_total

    # Check for duplicate snapshots
    metadata_hash = calculate_metadata_hash(files_metadata)
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Check if snapshot with same files already exists
        cursor.execute('''
            SELECT id FROM snapshots WHERE hash_metadata = ?
        ''', (metadata_hash,))
        existing = cursor.fetchone()
        
        if existing:
            # Clean up the created directory since it's a duplicate
            shutil.rmtree(snapshot_dir, ignore_errors=True)
            return existing['id'], f"Snapshot already exists (ID: {existing['id']})"

        # Insert snapshot
        cursor.execute('''
            INSERT INTO snapshots (name, description, branch_count, file_count, total_records, total_balance, hash_metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            snapshot_name,
            description,
            len(branch_codes),
            len(file_paths),
            total_records,
            total_balance,
            metadata_hash,
        ))
        
        snapshot_id = cursor.lastrowid

        # Insert file metadata with paths
        for file_meta in files_metadata:
            cursor.execute('''
                INSERT INTO snapshot_files (snapshot_id, file_name, file_hash, file_path, branch_code, record_count, branch_total)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                snapshot_id,
                file_meta['file_name'],
                file_meta['file_hash'],
                file_meta['file_path'],
                file_meta['branch_code'],
                file_meta['record_count'],
                file_meta['branch_total'],
            ))

        conn.commit()

    return snapshot_id, f"Snapshot created successfully (ID: {snapshot_id})"


def list_snapshots() -> pd.DataFrame:
    """
    List all snapshots with their metadata.
    
    Returns:
        DataFrame with snapshot information
    """
    with get_db_connection() as conn:
        query = '''
            SELECT 
                id,
                name,
                description,
                created_at,
                branch_count,
                file_count,
                total_records,
                total_balance
            FROM snapshots
            ORDER BY created_at DESC
        '''
        return pd.read_sql(query, conn)


def get_snapshot_details(snapshot_id: int) -> Dict:
    """
    Get detailed information about a specific snapshot.
    
    Args:
        snapshot_id: ID of the snapshot
        
    Returns:
        Dictionary with snapshot details and file list
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Get snapshot info
        cursor.execute('''
            SELECT * FROM snapshots WHERE id = ?
        ''', (snapshot_id,))
        snapshot = cursor.fetchone()
        
        if not snapshot:
            raise ValueError(f"Snapshot not found: {snapshot_id}")
        
        # Get files in snapshot
        cursor.execute('''
            SELECT file_name, branch_code, record_count, branch_total
            FROM snapshot_files
            WHERE snapshot_id = ?
            ORDER BY branch_code
        ''', (snapshot_id,))
        files = cursor.fetchall()

    return {
        'id': snapshot['id'],
        'name': snapshot['name'],
        'description': snapshot['description'],
        'created_at': snapshot['created_at'],
        'branch_count': snapshot['branch_count'],
        'file_count': snapshot['file_count'],
        'total_records': snapshot['total_records'],
        'total_balance': snapshot['total_balance'],
        'files': [dict(f) for f in files],
    }


def validate_snapshot_pair(snapshot_id_1: int, snapshot_id_2: int) -> Tuple[bool, str]:
    """
    Validate that two snapshots can be compared.
    
    Conditions:
    - Both snapshots must exist
    - Must have same number of files
    - Must have same branch codes
    - Branch codes must match
    
    Args:
        snapshot_id_1: First snapshot ID
        snapshot_id_2: Second snapshot ID
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        details_1 = get_snapshot_details(snapshot_id_1)
        details_2 = get_snapshot_details(snapshot_id_2)
    except ValueError as e:
        return False, str(e)

    # Check file count
    if details_1['file_count'] != details_2['file_count']:
        return False, f"File count mismatch: {details_1['file_count']} vs {details_2['file_count']}"

    # Check branch codes match
    branches_1 = sorted([f['branch_code'] for f in details_1['files']])
    branches_2 = sorted([f['branch_code'] for f in details_2['files']])
    
    if branches_1 != branches_2:
        return False, f"Branch codes don't match. S1: {branches_1}, S2: {branches_2}"

    return True, "Valid pair for comparison"


def get_snapshot_files(snapshot_id: int) -> List[str]:
    """
    Get list of file paths in a snapshot.
    
    Args:
        snapshot_id: ID of the snapshot
        
    Returns:
        List of file paths
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT file_path FROM snapshot_files
            WHERE snapshot_id = ?
            ORDER BY branch_code
        ''', (snapshot_id,))
        rows = cursor.fetchall()
    
    file_paths = [row['file_path'] for row in rows if row['file_path']]
    # Validate that files still exist
    return [path for path in file_paths if os.path.exists(path)]


def get_snapshot_file_names(snapshot_id: int) -> List[str]:
    """
    Get list of file names in a snapshot.
    
    Args:
        snapshot_id: ID of the snapshot
        
    Returns:
        List of file names
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT file_name FROM snapshot_files
            WHERE snapshot_id = ?
            ORDER BY branch_code
        ''', (snapshot_id,))
        rows = cursor.fetchall()
    
    return [row['file_name'] for row in rows]


def delete_snapshot(snapshot_id: int) -> str:
    """
    Delete a snapshot, its associated data, and physical files.
    
    Args:
        snapshot_id: ID of the snapshot to delete
        
    Returns:
        Status message
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Get file paths before deleting
        cursor.execute('SELECT file_path FROM snapshot_files WHERE snapshot_id = ?', (snapshot_id,))
        file_rows = cursor.fetchall()
        
        # Check if snapshot exists
        cursor.execute('SELECT id FROM snapshots WHERE id = ?', (snapshot_id,))
        if not cursor.fetchone():
            raise ValueError(f"Snapshot not found: {snapshot_id}")
        
        # Delete snapshot files (cascade should handle this, but explicit for clarity)
        cursor.execute('DELETE FROM snapshot_files WHERE snapshot_id = ?', (snapshot_id,))
        
        # Delete snapshot
        cursor.execute('DELETE FROM snapshots WHERE id = ?', (snapshot_id,))
        
        conn.commit()
    
    # Delete physical files
    for row in file_rows:
        if row['file_path'] and os.path.exists(row['file_path']):
            try:
                os.remove(row['file_path'])
            except Exception as e:
                # Log but don't fail if file deletion fails
                print(f"Warning: Could not delete file {row['file_path']}: {e}")
    
    # Try to delete snapshot directory if empty
    try:
        for snapshot_dir in SNAPSHOTS_STORAGE_DIR.iterdir():
            if snapshot_dir.is_dir() and not any(snapshot_dir.iterdir()):
                snapshot_dir.rmdir()
    except Exception:
        pass
    
    return f"Snapshot {snapshot_id} deleted successfully"


def export_snapshot_metadata(snapshot_id: int) -> Dict:
    """
    Export complete metadata of a snapshot for documentation.
    
    Args:
        snapshot_id: ID of the snapshot
        
    Returns:
        Dictionary with complete metadata
    """
    details = get_snapshot_details(snapshot_id)
    return {
        'snapshot': {
            'id': details['id'],
            'name': details['name'],
            'description': details['description'],
            'created_at': details['created_at'],
            'branch_count': details['branch_count'],
            'file_count': details['file_count'],
            'total_records': details['total_records'],
            'total_balance': details['total_balance'],
        },
        'files': details['files'],
    }


# Initialize tables on module load
init_snapshot_tables()
