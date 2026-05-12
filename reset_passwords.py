#!/usr/bin/env python3
"""Reset all user passwords"""

import sqlite3
from auth_manager import hash_password

DATABASE_FILE = 'app_database.db'

conn = sqlite3.connect(DATABASE_FILE)
cursor = conn.cursor()

# List of users to reset
users_to_reset = [
    ('admin', 'admin123'),
    ('manager_a', 'pass123'),
    ('analyst_dpt', 'pass123'),
    ('viewer_test', 'pass123'),
]

print("Resetting passwords for all users...\n")

for username, password in users_to_reset:
    password_hash = hash_password(password)
    cursor.execute("UPDATE users SET password_hash = ? WHERE username = ?", (password_hash, username))
    conn.commit()
    print(f"✅ Reset {username:15} → {password}")

print("\n" + "="*60)
print("✅ All passwords reset successfully!")
print("\n📋 Login credentials:")
print("-"*60)
print("  admin      → admin123")
print("  manager_a  → pass123")
print("  analyst_dpt → pass123")
print("  viewer_test → pass123")
print("-"*60)

conn.close()
