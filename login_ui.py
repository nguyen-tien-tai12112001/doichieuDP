"""
Login and role-based UI components.
"""

import streamlit as st
from auth_manager import authenticate_user, has_permission, can_access_branch, get_accessible_branches


def render_login_page():
    """Render login page."""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
            <div class="login-container">
                <h2 style="text-align: center; color: #1f77b4;">🔐 Hệ Thống So Sánh Tiền Gửi</h2>
                <p style="text-align: center; color: #666;">Đăng nhập để truy cập hệ thống</p>
            </div>
        """, unsafe_allow_html=True)
        
        st.divider()
        
        with st.form("login_form"):
            username = st.text_input('👤 Tên đăng nhập', placeholder='username', key='login_username')
            password = st.text_input('🔑 Mật khẩu', type='password', placeholder='password', key='login_password')
            
            col1, col2 = st.columns(2)
            with col1:
                submit_btn = st.form_submit_button('🚀 Đăng nhập', use_container_width=True, type='primary')
            
            if submit_btn:
                if not username or not password:
                    st.error('❌ Vui lòng nhập đầy đủ thông tin')
                else:
                    user = authenticate_user(username, password)
                    
                    if user:
                        st.session_state['logged_in'] = True
                        st.session_state['current_user'] = user
                        st.success(f"✅ Đăng nhập thành công! Xin chào {user['full_name']}")
                        st.rerun()
                    else:
                        st.error('❌ Tên đăng nhập hoặc mật khẩu không chính xác')
        
        st.markdown("---")
        st.caption("💡 Mẹo: Liên hệ admin để được cấp tài khoản")


def render_logout_button():
    """Render logout button in sidebar."""
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button('🚪 Đăng xuất', use_container_width=True, key='logout_btn'):
            st.session_state.clear()
            st.rerun()


def render_user_info_header():
    """Render user info in header."""
    user = st.session_state.get('current_user', {})
    
    if user:
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            role_emoji = {
                'ADMIN': '👑',
                'MANAGER': '👔',
                'ANALYST': '📊',
                'VIEWER': '👁️'
            }
            emoji = role_emoji.get(user['role'], '👤')
            st.caption(f"{emoji} {user['full_name']} ({user['role']})")
        
        with col3:
            render_logout_button()


def check_permission(permission: str) -> bool:
    """Check if current user has permission. Return False if denied."""
    user = st.session_state.get('current_user')
    
    if not user:
        return False
    
    if not has_permission(user, permission):
        st.error(f"❌ Bạn không có quyền '{permission}'")
        return False
    
    return True


def get_branch_filter(all_branches: list) -> list:
    """Get filtered branches based on user access."""
    user = st.session_state.get('current_user')
    
    if not user:
        return []
    
    if user['role'] == 'ADMIN':
        return all_branches
    
    accessible = get_accessible_branches(user)
    if accessible is None:  # None means all
        return all_branches
    
    # Filter to only accessible branches
    return [b for b in all_branches if b in accessible]


def render_branch_selector(all_branches: list) -> str:
    """Render branch selector based on user permissions."""
    user = st.session_state.get('current_user')
    
    if not user:
        return None
    
    filtered_branches = get_branch_filter(all_branches)
    
    if not filtered_branches:
        st.warning('⚠️ Bạn không có quyền truy cập chi nhánh nào')
        return None
    
    if user['role'] == 'ADMIN' or len(filtered_branches) > 1:
        selected = st.selectbox(
            '🏢 Chọn chi nhánh:',
            options=filtered_branches,
            key='branch_filter'
        )
        return selected
    else:
        # Only one branch, don't show selector
        st.info(f'📍 Bạn đang làm việc với chi nhánh: **{filtered_branches[0]}**')
        return filtered_branches[0]


def enforce_branch_access(branch_code: str) -> bool:
    """Enforce branch-level access. Return False if denied."""
    user = st.session_state.get('current_user')
    
    if not user:
        return False
    
    if not can_access_branch(user, branch_code):
        st.error(f"❌ Bạn không có quyền truy cập chi nhánh {branch_code}")
        return False
    
    return True


if __name__ == '__main__':
    # Test login
    if 'logged_in' not in st.session_state:
        render_login_page()
    else:
        user = st.session_state.get('current_user', {})
        st.success(f"Hello {user.get('full_name', 'Guest')}")
        render_logout_button()
