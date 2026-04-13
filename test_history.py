#!/usr/bin/env python3
"""Test script for history loading functionality."""

import sys
import os
sys.path.append(os.path.dirname(__file__))

# Test imports
try:
    from app import save_processed_data, load_processed_data, CACHE_DIR
    print("✅ Imports successful")
except Exception as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

# Test cache directory creation
if CACHE_DIR.exists():
    print("✅ Cache directory exists")
else:
    print("❌ Cache directory not created")

# Test save/load functionality
test_data = {"test": "data", "comparison": "df"}
test_key = "test_key_123"

try:
    save_processed_data(test_key, test_data)
    loaded_data = load_processed_data(test_key)
    if loaded_data == test_data:
        print("✅ Save/load functionality works")
    else:
        print("❌ Save/load data mismatch")
except Exception as e:
    print(f"❌ Save/load error: {e}")

print("Test completed!")