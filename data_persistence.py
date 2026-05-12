"""
Data persistence utilities for Streamlit Cloud deployment.
Handles database and file storage across deployments.
"""

import os
import pickle
import json
from pathlib import Path
from datetime import datetime
import sqlite3
import streamlit as st


# Detect if running on Streamlit Cloud
IS_STREAMLIT_CLOUD = 'STREAMLIT_SERVER_HEADLESS' in os.environ


class LocalDataManager:
    """Manage data persistence locally and on Streamlit Cloud."""
    
    def __init__(self, data_dir: str = 'data_warehouse'):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # Session data backup location
        self.backup_dir = self.data_dir / 'backups'
        self.backup_dir.mkdir(exist_ok=True)
    
    def save_pickle(self, data, filename: str):
        """Save data as pickle file."""
        filepath = self.data_dir / filename
        with open(filepath, 'wb') as f:
            pickle.dump(data, f)
        return str(filepath)
    
    def load_pickle(self, filename: str):
        """Load pickle file."""
        filepath = self.data_dir / filename
        if filepath.exists():
            with open(filepath, 'rb') as f:
                return pickle.load(f)
        return None
    
    def save_json(self, data, filename: str):
        """Save data as JSON file."""
        filepath = self.data_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        return str(filepath)
    
    def load_json(self, filename: str):
        """Load JSON file."""
        filepath = self.data_dir / filename
        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    
    def save_session_backup(self, session_key: str = 'comparison_results'):
        """Backup current session state."""
        if session_key in st.session_state:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = f'{session_key}_{timestamp}.pickle'
            self.save_pickle(st.session_state[session_key], f'backups/{backup_file}')
            return backup_file
        return None
    
    def list_backups(self, prefix: str = ''):
        """List all backup files."""
        backups = list(self.backup_dir.glob(f'{prefix}*.pickle'))
        return sorted(backups, key=lambda x: x.stat().st_mtime, reverse=True)
    
    def cleanup_old_backups(self, keep: int = 5):
        """Keep only last N backups."""
        backups = self.list_backups()
        if len(backups) > keep:
            for backup in backups[keep:]:
                backup.unlink()  # Delete file


class DatabaseManager:
    """Manage SQLite database with backup capabilities."""
    
    def __init__(self, db_path: str = 'app_database.db'):
        self.db_path = Path(db_path)
        self.backup_dir = Path('data_warehouse/db_backups')
        self.backup_dir.mkdir(exist_ok=True)
    
    def backup_database(self):
        """Create database backup."""
        if self.db_path.exists():
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = self.backup_dir / f'db_backup_{timestamp}.db'
            
            try:
                # SQLite backup protocol
                conn = sqlite3.connect(str(self.db_path))
                backup_conn = sqlite3.connect(str(backup_path))
                with backup_conn:
                    conn.backup(backup_conn)
                backup_conn.close()
                conn.close()
                return str(backup_path)
            except Exception as e:
                st.error(f"Backup failed: {str(e)}")
                return None
        return None
    
    def restore_database(self, backup_path: str):
        """Restore database from backup."""
        backup = Path(backup_path)
        if backup.exists():
            try:
                backup_conn = sqlite3.connect(str(backup))
                conn = sqlite3.connect(str(self.db_path))
                with conn:
                    backup_conn.backup(conn)
                conn.close()
                backup_conn.close()
                return True
            except Exception as e:
                st.error(f"Restore failed: {str(e)}")
                return False
        return False
    
    def get_backup_size(self):
        """Get total size of all backups."""
        if self.backup_dir.exists():
            total_size = sum(f.stat().st_size for f in self.backup_dir.glob('*.db'))
            return total_size / (1024 * 1024)  # Convert to MB
        return 0
    
    def list_backups(self):
        """List all database backups."""
        backups = list(self.backup_dir.glob('db_backup_*.db'))
        return sorted(backups, key=lambda x: x.stat().st_mtime, reverse=True)


class SessionDataManager:
    """Manage Streamlit session state persistence."""
    
    @staticmethod
    def init_session():
        """Initialize session state variables."""
        if 'data_manager' not in st.session_state:
            st.session_state.data_manager = LocalDataManager()
        if 'db_manager' not in st.session_state:
            st.session_state.db_manager = DatabaseManager()
        if 'last_backup' not in st.session_state:
            st.session_state.last_backup = None
    
    @staticmethod
    def save_comparison_results(results: dict):
        """Save comparison results."""
        data_manager = st.session_state.get('data_manager', LocalDataManager())
        st.session_state.comparison_results = results
        backup_file = data_manager.save_session_backup('comparison_results')
        st.session_state.last_backup = backup_file
        return backup_file
    
    @staticmethod
    def load_last_results():
        """Load last saved results."""
        data_manager = st.session_state.get('data_manager', LocalDataManager())
        backups = data_manager.list_backups('comparison_results')
        if backups:
            return data_manager.load_pickle(f'backups/{backups[0].name}')
        return None


# Helper function for app initialization
def init_data_persistence():
    """Initialize all data persistence managers."""
    SessionDataManager.init_session()
    
    # Auto-backup database periodically
    if 'backup_counter' not in st.session_state:
        st.session_state.backup_counter = 0
    
    st.session_state.backup_counter += 1
    
    # Backup every 10 page loads
    if st.session_state.backup_counter >= 10:
        db_manager = st.session_state.db_manager
        backup_path = db_manager.backup_database()
        if backup_path:
            st.session_state.last_backup = backup_path
        st.session_state.backup_counter = 0
        
        # Cleanup old backups
        db_manager.list_backups()
        if len(db_manager.list_backups()) > 5:
            for old_backup in db_manager.list_backups()[5:]:
                old_backup.unlink()
