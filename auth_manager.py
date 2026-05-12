"""
Authentication and authorization manager.
Handles user login, roles, and branch-level access control.
"""

import sqlite3
import hashlib
import hmac
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

# Try to import bcrypt, fall back to hashlib if not available
try:
    import bcrypt
    HAS_BCRYPT = True
except ImportError:
    HAS_BCRYPT = False

DATABASE_FILE = Path('app_database.db')

# Role definitions
ROLES = {
    'ADMIN': {
        'description': 'Quản trị viên toàn bộ hệ thống',
        'permissions': ['*'],
    },
    'MANAGER': {
        'description': 'Quản lý chi nhánh',
        'permissions': [
            'dashboard.view', 'warehouse.view', 'warehouse.import', 'warehouse.delete', 'warehouse.manage_tags',
            'comparison.run', 'analysis.view', 'ai.view', 'report.view', 'report.export',
            'report.share', 'settings.history',
            'import', 'export', 'compare', 'create_report', 'view_report'
        ],
    },
    'ANALYST': {
        'description': 'Phân tích dữ liệu',
        'permissions': [
            'dashboard.view', 'warehouse.view', 'comparison.run', 'analysis.view',
            'ai.view', 'report.view', 'report.export', 'settings.history',
            'compare', 'export', 'view_report'
        ],
    },
    'OPERATOR': {
        'description': 'Vận hành kho dữ liệu',
        'permissions': [
            'dashboard.view', 'warehouse.view', 'warehouse.import', 'warehouse.delete',
            'warehouse.manage_tags', 'settings.history',
            'import', 'view_report'
        ],
    },
    'VIEWER': {
        'description': 'Xem báo cáo',
        'permissions': ['dashboard.view', 'analysis.view', 'report.view', 'view_report'],
    },
    'AUDITOR': {
        'description': 'Kiểm toán và xem lịch sử',
        'permissions': [
            'dashboard.view', 'warehouse.view', 'analysis.view', 'report.view',
            'settings.history', 'admin.audit', 'audit_log', 'view_report'
        ],
    },
}


def init_auth_tables():
    """Initialize authentication tables if they don't exist."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    try:
        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'VIEWER',
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                failed_login_attempts INTEGER DEFAULT 0,
                locked_until TIMESTAMP
            )
        """)
        
        # Branch access table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS branch_access (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                branch_code TEXT NOT NULL,
                access_level TEXT DEFAULT 'VIEW',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                UNIQUE(user_id, branch_code)
            )
        """)
        
        # Audit log table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                target_type TEXT,
                target_id INTEGER,
                branch_code TEXT,
                details TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        conn.commit()
        print("Auth tables initialized successfully")
    except Exception as e:
        print(f"Error initializing auth tables: {str(e)}")
    finally:
        conn.close()


def hash_password(password: str) -> str:
    """Hash a password using bcrypt or fallback to PBKDF2."""
    if HAS_BCRYPT:
        try:
            salt = bcrypt.gensalt(rounds=12)
            return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
        except Exception:
            pass
    
    # Fallback: Use PBKDF2 (built-in)
    import secrets
    salt = secrets.token_hex(16)
    pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode(), 100000)
    return f"pbkdf2:sha256:100000${salt}${pwd_hash.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its hash (bcrypt or PBKDF2)."""
    if HAS_BCRYPT and password_hash.startswith('$2'):  # bcrypt format
        try:
            return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
        except Exception:
            return False
    
    # Fallback: Verify PBKDF2 hash
    if password_hash.startswith('pbkdf2:'):
        try:
            parts = password_hash.split('$')
            if len(parts) != 3:
                return False
            salt = parts[1]
            stored_hash = parts[2]
            pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode(), 100000)
            return pwd_hash.hex() == stored_hash
        except Exception:
            return False
    
    # Try bcrypt for existing hashes
    if HAS_BCRYPT:
        try:
            return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
        except Exception:
            return False
    
    return False


def create_user(username: str, email: str, password: str, full_name: str, role: str = 'VIEWER') -> Tuple[bool, str]:
    """Create a new user."""
    if role not in ROLES:
        return False, f"❌ Role '{role}' không tồn tại"
    
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    try:
        password_hash = hash_password(password)
        cursor.execute("""
            INSERT INTO users (username, email, password_hash, full_name, role)
            VALUES (?, ?, ?, ?, ?)
        """, (username, email, password_hash, full_name, role))
        conn.commit()
        
        # Get the new user ID
        user_id = cursor.lastrowid
        
        # Log action
        log_audit('SYSTEM', 'CREATE_USER', 'user', user_id, None, f"Created user {username} with role {role}")
        
        return True, f"✅ Tạo user '{username}' thành công"
    except sqlite3.IntegrityError as e:
        if 'username' in str(e):
            return False, f"❌ Username '{username}' đã tồn tại"
        elif 'email' in str(e):
            return False, f"❌ Email '{email}' đã tồn tại"
        else:
            return False, f"❌ Lỗi: {str(e)}"
    except Exception as e:
        return False, f"❌ Lỗi tạo user: {str(e)}"
    finally:
        conn.close()


def authenticate_user(username: str, password: str) -> Optional[Dict]:
    """Authenticate a user and return their info if valid."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT id, username, email, full_name, role, is_active, locked_until, failed_login_attempts
            FROM users
            WHERE username = ?
        """, (username,))
        
        user = cursor.fetchone()
        
        if not user:
            return None
        
        user_id, uname, email, full_name, role, is_active, locked_until, failed_attempts = user
        
        # Check if account is locked
        if locked_until:
            from datetime import datetime
            if datetime.fromisoformat(locked_until) > datetime.now():
                return None  # Account still locked
        
        # Check if user is active
        if not is_active:
            return None
        
        # Fetch password hash
        cursor.execute("SELECT password_hash FROM users WHERE id = ?", (user_id,))
        password_hash = cursor.fetchone()[0]
        
        # Verify password
        if not verify_password(password, password_hash):
            # Increment failed login attempts
            cursor.execute("""
                UPDATE users
                SET failed_login_attempts = failed_login_attempts + 1
                WHERE id = ?
            """, (user_id,))
            
            # Lock account if 5 failed attempts
            if failed_attempts >= 4:
                from datetime import datetime, timedelta
                lock_until = (datetime.now() + timedelta(minutes=30)).isoformat()
                cursor.execute("""
                    UPDATE users
                    SET locked_until = ?
                    WHERE id = ?
                """, (lock_until, user_id))
            
            conn.commit()
            return None
        
        # Successful login - reset failure counter
        cursor.execute("""
            UPDATE users
            SET failed_login_attempts = 0, locked_until = NULL, last_login = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (user_id,))
        conn.commit()
        
        # Get branch access
        cursor.execute("""
            SELECT branch_code FROM branch_access WHERE user_id = ?
        """, (user_id,))
        accessible_branches = [row[0] for row in cursor.fetchall()]
        
        # Log successful login
        log_audit(user_id, 'LOGIN', 'user', user_id, None, f"Login successful")
        
        return {
            'id': user_id,
            'username': uname,
            'email': email,
            'full_name': full_name,
            'role': role,
            'accessible_branches': accessible_branches if accessible_branches else None,  # None = all branches (admin)
        }
    except Exception as e:
        print(f"Authentication error: {str(e)}")
        return None
    finally:
        conn.close()


def get_user(user_id: int) -> Optional[Dict]:
    """Get user info by ID."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT id, username, email, full_name, role, is_active
            FROM users
            WHERE id = ?
        """, (user_id,))
        
        row = cursor.fetchone()
        if not row:
            return None
        
        user_id, username, email, full_name, role, is_active = row
        
        # Get branches
        cursor.execute("""
            SELECT branch_code FROM branch_access WHERE user_id = ?
        """, (user_id,))
        accessible_branches = [r[0] for r in cursor.fetchall()]
        
        return {
            'id': user_id,
            'username': username,
            'email': email,
            'full_name': full_name,
            'role': role,
            'is_active': is_active,
            'accessible_branches': accessible_branches,
        }
    except Exception as e:
        print(f"Error fetching user: {str(e)}")
        return None
    finally:
        conn.close()


def list_all_users() -> List[Dict]:
    """List all users (Admin only)."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT id, username, email, full_name, role, is_active, created_at, last_login
            FROM users
            ORDER BY created_at DESC
        """)
        
        users = []
        for row in cursor.fetchall():
            user_id, username, email, full_name, role, is_active, created_at, last_login = row
            
            # Get branches for this user
            cursor.execute("""
                SELECT GROUP_CONCAT(branch_code, ', ') FROM branch_access WHERE user_id = ?
            """, (user_id,))
            branches_result = cursor.fetchone()
            branches = branches_result[0] if branches_result and branches_result[0] else "Tất cả"
            
            users.append({
                'id': user_id,
                'username': username,
                'email': email,
                'full_name': full_name,
                'role': role,
                'is_active': is_active,
                'branches': branches,
                'created_at': created_at,
                'last_login': last_login,
            })
        
        return users
    except Exception as e:
        print(f"Error listing users: {str(e)}")
        return []
    finally:
        conn.close()


def update_user_role(user_id: int, new_role: str) -> Tuple[bool, str]:
    """Update a user's role."""
    if new_role not in ROLES:
        return False, f"❌ Role '{new_role}' không tồn tại"
    
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE users
            SET role = ?
            WHERE id = ?
        """, (new_role, user_id))
        conn.commit()
        
        log_audit('SYSTEM', 'UPDATE_ROLE', 'user', user_id, None, f"Role changed to {new_role}")
        return True, f"✅ Cập nhật role thành công"
    except Exception as e:
        return False, f"❌ Lỗi: {str(e)}"
    finally:
        conn.close()


def set_branch_access(user_id: int, branch_code: str, access_level: str = 'VIEW') -> Tuple[bool, str]:
    """Grant user access to a specific branch."""
    if access_level not in ['VIEW', 'EDIT']:
        return False, f"❌ Access level '{access_level}' không hợp lệ"
    
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT OR REPLACE INTO branch_access (user_id, branch_code, access_level)
            VALUES (?, ?, ?)
        """, (user_id, branch_code, access_level))
        conn.commit()
        
        log_audit('SYSTEM', 'GRANT_BRANCH_ACCESS', 'branch', None, branch_code, 
                 f"User {user_id} granted {access_level} access to {branch_code}")
        return True, f"✅ Cấp quyền cho chi nhánh {branch_code} thành công"
    except Exception as e:
        return False, f"❌ Lỗi: {str(e)}"
    finally:
        conn.close()


def remove_branch_access(user_id: int, branch_code: str) -> Tuple[bool, str]:
    """Remove user's access to a branch."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            DELETE FROM branch_access
            WHERE user_id = ? AND branch_code = ?
        """, (user_id, branch_code))
        conn.commit()
        
        log_audit('SYSTEM', 'REVOKE_BRANCH_ACCESS', 'branch', None, branch_code,
                 f"User {user_id} revoked access to {branch_code}")
        return True, f"✅ Thu hồi quyền cho chi nhánh {branch_code} thành công"
    except Exception as e:
        return False, f"❌ Lỗi: {str(e)}"
    finally:
        conn.close()


def deactivate_user(user_id: int) -> Tuple[bool, str]:
    """Deactivate a user account."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    try:
        cursor.execute("UPDATE users SET is_active = 0 WHERE id = ?", (user_id,))
        conn.commit()
        
        log_audit('SYSTEM', 'DEACTIVATE_USER', 'user', user_id, None, "User account deactivated")
        return True, f"✅ Vô hiệu hóa user thành công"
    except Exception as e:
        return False, f"❌ Lỗi: {str(e)}"
    finally:
        conn.close()


def has_permission(user: Dict, permission: str) -> bool:
    """Check if user has a specific permission based on their role."""
    if user['role'] == 'ADMIN':
        return True  # Admins have all permissions
    
    role_permissions = ROLES.get(user['role'], {}).get('permissions', [])
    return '*' in role_permissions or permission in role_permissions


def can_access_branch(user: Dict, branch_code: str) -> bool:
    """Check if user can access a specific branch."""
    if user['role'] == 'ADMIN':
        return True  # Admins can access all branches
    
    # Check if user has branch access restrictions
    if user.get('accessible_branches') is None:
        return True  # No restrictions
    
    return branch_code in user['accessible_branches']


def get_accessible_branches(user: Dict) -> List[str]:
    """Get list of branches accessible to user."""
    if user['role'] == 'ADMIN':
        return None  # None means all branches
    
    return user.get('accessible_branches', [])


def log_audit(user_id, action: str, target_type: str, target_id: Optional[int], 
              branch_code: Optional[str], details: str) -> None:
    """Log an action to audit trail."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO audit_log (user_id, action, target_type, target_id, branch_code, details)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, action, target_type, target_id, branch_code, details))
        conn.commit()
    except Exception as e:
        print(f"Audit log error: {str(e)}")
    finally:
        conn.close()


def get_audit_logs(limit: int = 100, user_id: Optional[int] = None, 
                   action: Optional[str] = None) -> List[Dict]:
    """Retrieve audit logs (Admin only)."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    try:
        query = "SELECT user_id, action, branch_code, details, timestamp FROM audit_log"
        params = []
        
        conditions = []
        if user_id:
            conditions.append("user_id = ?")
            params.append(user_id)
        if action:
            conditions.append("action = ?")
            params.append(action)
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        
        logs = []
        for row in cursor.fetchall():
            user_id, act, branch, details, timestamp = row
            logs.append({
                'user_id': user_id,
                'action': act,
                'branch_code': branch,
                'details': details,
                'timestamp': timestamp,
            })
        
        return logs
    except Exception as e:
        print(f"Error fetching audit logs: {str(e)}")
        return []
    finally:
        conn.close()


if __name__ == '__main__':
    # Initialize tables
    init_auth_tables()
    
    # Create default admin user (for first setup)
    success, msg = create_user('admin', 'admin@thidua.local', 'admin123', 'Administrator', 'ADMIN')
    print(msg)
