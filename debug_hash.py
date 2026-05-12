#!/usr/bin/env python3
"""Debug password hash issue"""

import sqlite3
conn = sqlite3.connect('app_database.db')
cursor = conn.cursor()

cursor.execute("SELECT username, password_hash FROM users WHERE username='admin'")
row = cursor.fetchone()
if row:
    print("Admin user:")
    print(f"  Username: {row[0]}")
    print(f"  Hash: {row[1][:50]}...")
    
    # Test hash and verify
    from auth_manager import hash_password, verify_password
    test_pwd = 'admin123'
    test_hash = hash_password(test_pwd)
    verify = verify_password(test_pwd, row[1])
    
    print(f"\nTest verify with stored hash: {verify}")
    print(f"New hash would be: {test_hash[:50]}...")
else:
    print("User not found")

conn.close()
