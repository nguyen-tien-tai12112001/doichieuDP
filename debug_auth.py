#!/usr/bin/env python3
"""Debug script to reset accounts and test auth"""
import sqlite3

conn = sqlite3.connect('app_database.db')
cursor = conn.cursor()

# Reset all accounts
print("Resetting account lockouts...")
cursor.execute("UPDATE users SET failed_login_attempts = 0, locked_until = NULL")
conn.commit()

# Show status
print("\nAccount status:")
cursor.execute("SELECT username, is_active, locked_until, failed_login_attempts FROM users")
for row in cursor.fetchall():
    print(f"  {row[0]:15} - Active: {row[1]}, Locked: {row[2]}, Failures: {row[3]}")

# Test auth
print("\nTesting authentication:")
from auth_manager import authenticate_user, verify_password
import sys

accounts = [
    ('admin', 'admin123'),
    ('manager_a', 'pass123'),
]

for username, password in accounts:
    # Get password hash from DB
    cursor.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    if result:
        pwd_hash = result[0]
        verify_result = verify_password(password, pwd_hash)
        print(f"  {username}: verify={verify_result}")
    
    # Test full auth
    user = authenticate_user(username, password)
    status = "✅" if user else "❌"
    print(f"  {status} {username} / {password}")

conn.close()
