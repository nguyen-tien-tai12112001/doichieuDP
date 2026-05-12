#!/usr/bin/env python3
"""Unlock all user accounts"""

import sqlite3

DATABASE_FILE = 'app_database.db'

conn = sqlite3.connect(DATABASE_FILE)
cursor = conn.cursor()

# Unlock all accounts
cursor.execute("""
    UPDATE users 
    SET failed_login_attempts = 0, locked_until = NULL
""")
conn.commit()

print("Unlocking all accounts...")
cursor.execute("SELECT username, failed_login_attempts, locked_until FROM users")
for row in cursor.fetchall():
    print(f"✅ {row[0]:15} - Failures: {row[1]}, Locked: {row[2]}")

print("\n✅ All accounts unlocked!")

conn.close()
