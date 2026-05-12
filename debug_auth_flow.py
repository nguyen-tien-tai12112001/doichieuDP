#!/usr/bin/env python3
"""Debug authenticate_user function"""

import sqlite3
from datetime import datetime

DATABASE_FILE = 'app_database.db'

conn = sqlite3.connect(DATABASE_FILE)
cursor = conn.cursor()

username = 'admin'
password = 'admin123'

print(f"Testing authentication for {username}...")

# Step 1: Get user
cursor.execute("""
    SELECT id, username, email, full_name, role, is_active, locked_until, failed_login_attempts
    FROM users
    WHERE username = ?
""", (username,))

user = cursor.fetchone()
print(f"\n1. User found: {user is not None}")

if not user:
    print("   ❌ User not found!")
else:
    user_id, uname, email, full_name, role, is_active, locked_until, failed_attempts = user
    print(f"   Username: {uname}")
    print(f"   Role: {role}")
    print(f"   Is active: {is_active}")
    print(f"   Locked until: {locked_until}")
    
    # Step 2: Check if locked
    if locked_until:
        if datetime.fromisoformat(locked_until) > datetime.now():
            print("   ❌ Account is LOCKED")
        else:
            print("   ✅ Lock expired, can login")
    else:
        print("   ✅ Not locked")
    
    # Step 3: Check if active
    if not is_active:
        print("   ❌ Account is INACTIVE")
    else:
        print("   ✅ Account is ACTIVE")
    
    # Step 4: Get password hash
    cursor.execute("SELECT password_hash FROM users WHERE id = ?", (user_id,))
    pwd_result = cursor.fetchone()
    if pwd_result:
        password_hash = pwd_result[0]
        print(f"\n2. Password hash found: True")
        
        # Step 5: Verify password
        from auth_manager import verify_password
        verify_result = verify_password(password, password_hash)
        print(f"\n3. Password verification: {verify_result}")
        
        if verify_result:
            print("   ✅ Password is CORRECT")
        else:
            print("   ❌ Password is WRONG")
    else:
        print("   ❌ Password hash not found")

conn.close()
