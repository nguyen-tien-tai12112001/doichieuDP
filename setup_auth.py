#!/usr/bin/env python3
"""
Setup script to initialize the application with default admin account.
Run this once after first deployment.
"""

import subprocess
import sys
from pathlib import Path

def setup_application(interactive=False):
    """Initialize application and create default admin user."""
    
    print("🚀 Initializing ThiDua Khen Thuong Application...")
    print("=" * 60)
    
    try:
        # Import and initialize auth
        from auth_manager import init_auth_tables, create_user, set_branch_access
        
        print("\n✅ Step 1: Initializing database tables...")
        init_auth_tables()
        
        print("\n✅ Step 2: Creating default admin account...")
        
        if interactive:
            username = 'admin'
            email = 'admin@thidua.local'
            password = input("🔑 Enter admin password (default: admin123): ").strip() or 'admin123'
            full_name = input("📝 Enter admin full name (default: Administrator): ").strip() or 'Administrator'
        else:
            username = 'admin'
            email = 'admin@thidua.local'
            password = 'admin123'
            full_name = 'Administrator'
        
        success, msg = create_user(username, email, password, full_name, 'ADMIN')
        print(f"   {msg}")
        
        if not success and "already exists" in msg.lower():
            print("   ℹ️ Admin account already exists, skipping creation")
        elif not success:
            print(f"   ❌ Failed to create admin account: {msg}")
            return False
        
        print("\n✅ Step 3: Setting up default branch access...")
        
        # Create test users with branch access
        test_users = [
            {
                'username': 'manager_a',
                'email': 'manager_a@thidua.local',
                'password': 'pass123',
                'full_name': 'Trần Võ A',
                'role': 'MANAGER',
                'branches': ['BRA001']
            },
            {
                'username': 'analyst_dpt',
                'email': 'analyst_dpt@thidua.local',
                'password': 'pass123',
                'full_name': 'Analyst Công ty',
                'role': 'ANALYST',
                'branches': ['BRA001', 'BRA002']
            },
            {
                'username': 'viewer_test',
                'email': 'viewer_test@thidua.local',
                'password': 'pass123',
                'full_name': 'Viewer Test',
                'role': 'VIEWER',
                'branches': ['BRA001']
            },
        ]
        
        for user_info in test_users:
            success, msg = create_user(
                user_info['username'],
                user_info['email'],
                user_info['password'],
                user_info['full_name'],
                user_info['role']
            )
            
            if success:
                # Get user ID (need to query db)
                from auth_manager import authenticate_user
                user = authenticate_user(user_info['username'], user_info['password'])
                if user:
                    for branch in user_info['branches']:
                        set_branch_access(user['id'], branch, 'VIEW')
                    print(f"   ✅ Created {user_info['role']:8} {user_info['username']:15} with branches: {', '.join(user_info['branches'])}")
            else:
                if "already exists" in msg.lower():
                    print(f"   ℹ️ User {user_info['username']} already exists")
                else:
                    print(f"   ❌ Failed to create {user_info['username']}: {msg}")
        
        print("\n" + "=" * 60)
        print("✅ Setup completed successfully!")
        print("\n📋 Default Accounts:")
        print("-" * 60)
        print(f"  ADMIN:      username='admin' password='{password}'")
        print(f"  MANAGER:    username='manager_a' password='pass123'")
        print(f"  ANALYST:    username='analyst_dpt' password='pass123'")
        print(f"  VIEWER:     username='viewer_test' password='pass123'")
        print("-" * 60)
        print("\n💡 Tip: Change these passwords after first login!")
        print("🚀 You can now run: streamlit run app.py")
        
        return True
    
    except Exception as e:
        print(f"\n❌ Setup failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    # Check for --interactive flag
    interactive = '--interactive' in sys.argv or '-i' in sys.argv
    success = setup_application(interactive=interactive)
    sys.exit(0 if success else 1)
