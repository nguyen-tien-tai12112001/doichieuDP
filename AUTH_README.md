# 🔐 Authentication & Authorization System

## Overview
**Level 2** Role-based Access Control (RBAC) with Branch-level security

### Features
- ✅ User login with password hashing (bcrypt)
- ✅ 4 built-in roles: ADMIN, MANAGER, ANALYST, VIEWER
- ✅ Branch-level access control (Row Security)
- ✅ Account lockout after 5 failed login attempts
- ✅ Admin panel for user management
- ✅ Audit logging for all actions

---

## 🏗️ Architecture

### Tables Created
1. **users** - User accounts with roles
2. **branch_access** - User-to-Branch permissions
3. **audit_log** - Action logging for compliance

### Roles & Permissions

| Role | Import | Export | Delete | Create Report | View Report | Data Filter | Admin Panel |
|------|--------|--------|--------|-------|-------|-------|-------|
| 👑 ADMIN | ✅ | ✅ | ✅ | ✅ | ✅ | All | ✅ |
| 👔 MANAGER | ✅ | ✅ | ❌ | ✅ | ✅ | Own Branch | ❌ |
| 📊 ANALYST | ❌ | ✅ | ❌ | ❌ | ✅ | Assigned | ❌ |
| 👁️ VIEWER | ❌ | ❌ | ❌ | ❌ | ✅ | Read-only | ❌ |

---

## 🚀 Quick Start

### 1. First-Time Setup
```bash
python setup_auth.py
```

This will:
- Create database tables
- Create admin account (default: `admin/admin123`)
- Create test users for each role
- Set up sample branch access

### 2. Run Application
```bash
streamlit run app.py
```

You'll see a login page. Use credentials created in setup.

---

## 👥 User Management

### Login Page
- **URL**: `http://localhost:8501` (redirects to login if not authenticated)
- **Default Admin**: `admin` / `admin123`

### Admin Panel
After login as ADMIN, see **👑 Admin Panel** in sidebar:

#### Tab 1: 👥 Người dùng
- View all users
- Create new user
- Update role
- Deactivate account

#### Tab 2: 🔐 Quyền hạn
- Assign branches to users
- Control read/write permissions per branch

#### Tab 3: 📋 Audit Log
- Track all actions (login, import, export, etc.)
- Filter by user or action type
- Timestamp for compliance

---

## 🔑 Authentication Flow

```
1. User enters username & password
2. System checks:
   - Account exists
   - Account is active
   - Account not locked
3. Verify password hash (bcrypt)
4. On success:
   - Update last_login timestamp
   - Reset failed_login_attempts counter
   - Store in session_state
5. On failure:
   - Increment failed_login_attempts
   - Lock account after 5 failures (30 min)
6. All logins logged in audit_log
```

---

## 🛡️ Data Security

### Branch-Level Row Security
Filter shown data based on user role:

```python
# Example: Data loading with branch filter
if user['role'] == 'ADMIN':
    # See all branches
    branches = all_branches
elif user['accessible_branches']:
    # See only assigned branches
    branches = user['accessible_branches']
```

### Features Visibility
- **ADMIN sees**: Full warehouse, all users, audit logs, admin panel
- **MANAGER sees**: Own branch warehouse, compare tools, can export
- **ANALYST sees**: Assigned branches, comparison & analysis tools
- **VIEWER sees**: Published reports only

---

## 📝 Code Usage

### Check User Permission
```python
from login_ui import check_permission

if check_permission('export'):
    # User can export
    export_to_excel(data)
```

### Filter by Branch
```python
from login_ui import get_branch_filter, render_branch_selector

branches = get_branch_filter(all_branches)
selected_branch = render_branch_selector(branches)
```

### Enforce Branch Access
```python
from login_ui import enforce_branch_access

if enforce_branch_access(branch_code):
    # Load data for this branch
    ...
```

### Log Actions
```python
from auth_manager import log_audit

log_audit(user_id, 'IMPORT_FILE', 'file', file_id, branch_code, 'Imported Q1_2024 data')
```

---

## 🔄 Account Lifecycle

### Creating User
```python
from auth_manager import create_user

success, msg = create_user(
    username='john_doe',
    email='john@company.com',
    password='SecurePass123',
    full_name='John Doe',
    role='ANALYST'
)
```

### Assigning Branches
```python
from auth_manager import set_branch_access

set_branch_access(user_id, 'BRA001', 'VIEW')  # Read-only
set_branch_access(user_id, 'BRA002', 'EDIT')  # Can edit
```

### Account Lock & Reset
```python
from auth_manager import deactivate_user, get_user

# Deactivate account
deactivate_user(user_id)

# Check status
user_info = get_user(user_id)
if user_info['is_active']:
    print("Account is active")
```

---

## 📊 Audit Log

All actions are logged:
- **Login** - User authentication
- **CREATE_USER** - New account creation
- **UPDATE_ROLE** - Role changes
- **GRANT_BRANCH_ACCESS** - Permission grants
- **IMPORT_FILE** - Data imports
- **EXPORT_REPORT** - Report exports
- **DELETE_FILE** - Data deletions

Query logs:
```python
from auth_manager import get_audit_logs

# Get recent logs
logs = get_audit_logs(limit=50)

# Filter by user
logs = get_audit_logs(user_id=123)

# Filter by action
logs = get_audit_logs(action='IMPORT_FILE')
```

---

## 🔒 Security Best Practices

1. **Change Default Passwords** ⚠️
   - Default admin password is `admin123`
   - Change immediately after first login

2. **Strong Passwords**
   - Users should use 8+ characters
   - Mix of letters, numbers, symbols

3. **Regular Audits**
   - Review audit logs weekly
   - Check for unauthorized access attempts

4. **Account Management**
   - Deactivate unused accounts
   - Review branch assignments periodically

5. **Session Timeout** (Future)
   - Currently 30 min of inactivity = auto logout
   - Will implement in Level 3

---

## 🐛 Troubleshooting

### "Account Locked" Message
→ 5 failed password attempts. Wait 30 minutes or contact admin.

### User Can't See Branch Data
→ Admin needs to grant branch access:
1. Open Admin Panel → 🔐 Quyền hạn
2. Select user → Select branch → Save

### Forgotten Admin Password
→ Developer access:
```python
from auth_manager import hash_password, init_auth_tables
import sqlite3

conn = sqlite3.connect('app_database.db')
cursor = conn.cursor()
new_hash = hash_password('newpassword123')
cursor.execute("UPDATE users SET password_hash = ? WHERE username = ?", 
               (new_hash, 'admin'))
conn.commit()
```

---

## 📈 Future Enhancements (Level 3)

- [ ] Password expiration (90 days)
- [ ] 2FA (OTP via email)
- [ ] Session timeout enforcement
- [ ] Login history & IP tracking
- [ ] Role templates
- [ ] Permission inheritance
- [ ] LDAP/Active Directory integration
- [ ] API token authentication

---

## 📞 Support

For issues or questions:
1. Check audit logs for what went wrong
2. Review this README
3. Contact system administrator

**Last Updated**: April 28, 2026
**Version**: 2.0 (RBAC + Branch Security)
