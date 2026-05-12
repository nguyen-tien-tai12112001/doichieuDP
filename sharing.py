"""Collaboration and sharing module for deposit analysis."""

import streamlit as st
import pandas as pd
import json
import hashlib
import secrets
import string
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import sqlite3
from pathlib import Path
import pickle


class ShareManager:
    """Manages shared analysis sessions and comments."""

    def __init__(self, db_path: str = "shared_sessions.db"):
        self.db_path = Path(db_path)
        self._init_db()

    def _init_db(self):
        """Initialize the database for shared sessions."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    password_hash TEXT,
                    created_at TIMESTAMP,
                    expires_at TIMESTAMP,
                    data_pickle BLOB,
                    title TEXT,
                    description TEXT
                )
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS comments (
                    comment_id TEXT PRIMARY KEY,
                    session_id TEXT,
                    user_name TEXT,
                    comment TEXT,
                    created_at TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
                )
            ''')

    def create_shared_session(self, data: Dict, title: str = "", description: str = "",
                            password: Optional[str] = None, expiry_days: int = 7) -> Tuple[str, str]:
        """Create a new shared session and return session ID and password."""
        session_id = self._generate_session_id()
        password = password or self._generate_password()

        # Hash the password
        password_hash = hashlib.sha256(password.encode()).hexdigest()

        # Serialize data
        data_pickle = pickle.dumps(data)

        # Calculate expiry
        created_at = datetime.now()
        expires_at = created_at + timedelta(days=expiry_days)

        # Store in database
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO sessions (session_id, password_hash, created_at, expires_at, data_pickle, title, description)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (session_id, password_hash, created_at, expires_at, data_pickle, title, description))

        return session_id, password

    def load_shared_session(self, session_id: str, password: str) -> Optional[Dict]:
        """Load a shared session if password is correct and not expired."""
        password_hash = hashlib.sha256(password.encode()).hexdigest()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT data_pickle, expires_at FROM sessions
                WHERE session_id = ? AND password_hash = ?
            ''', (session_id, password_hash))

            result = cursor.fetchone()

            if result:
                data_pickle, expires_at = result
                if datetime.now() < datetime.fromisoformat(expires_at):
                    return pickle.loads(data_pickle)

        return None

    def add_comment(self, session_id: str, user_name: str, comment: str) -> bool:
        """Add a comment to a shared session."""
        comment_id = self._generate_comment_id()

        with sqlite3.connect(self.db_path) as conn:
            try:
                conn.execute('''
                    INSERT INTO comments (comment_id, session_id, user_name, comment, created_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', (comment_id, session_id, user_name, comment, datetime.now()))
                return True
            except sqlite3.IntegrityError:
                return False  # Session doesn't exist

    def get_comments(self, session_id: str) -> List[Dict]:
        """Get all comments for a session."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT user_name, comment, created_at FROM comments
                WHERE session_id = ? ORDER BY created_at DESC
            ''', (session_id,))

            return [
                {
                    'user_name': row[0],
                    'comment': row[1],
                    'created_at': row[2]
                }
                for row in cursor.fetchall()
            ]

    def get_session_info(self, session_id: str) -> Optional[Dict]:
        """Get session metadata without data."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT title, description, created_at, expires_at FROM sessions
                WHERE session_id = ?
            ''', (session_id,))

            result = cursor.fetchone()
            if result:
                title, description, created_at, expires_at = result
                return {
                    'title': title,
                    'description': description,
                    'created_at': created_at,
                    'expires_at': expires_at,
                    'is_expired': datetime.now() > datetime.fromisoformat(expires_at)
                }
        return None

    def _generate_session_id(self) -> str:
        """Generate a unique session ID."""
        return secrets.token_urlsafe(16)

    def _generate_comment_id(self) -> str:
        """Generate a unique comment ID."""
        return secrets.token_urlsafe(8)

    def _generate_password(self, length: int = 8) -> str:
        """Generate a random password."""
        chars = string.ascii_letters + string.digits
        return ''.join(secrets.choice(chars) for _ in range(length))


# Global share manager instance
share_manager = ShareManager()


def create_shareable_link(analysis_data: Dict, title: str = "Deposit Analysis",
                         description: str = "", password: Optional[str] = None) -> Tuple[str, str]:
    """Create a shareable link for analysis results."""
    session_id, generated_password = share_manager.create_shared_session(
        analysis_data, title, description, password
    )

    # Create a shareable URL (in a real app, this would be your domain)
    share_url = f"share/{session_id}"

    return share_url, generated_password


def load_shared_analysis(session_id: str, password: str) -> Optional[Dict]:
    """Load analysis from a shared session."""
    return share_manager.load_shared_session(session_id, password)


def add_collaboration_comment(session_id: str, user_name: str, comment: str) -> bool:
    """Add a comment to a shared analysis."""
    return share_manager.add_comment(session_id, user_name, comment)


def get_collaboration_comments(session_id: str) -> List[Dict]:
    """Get comments for a shared analysis."""
    return share_manager.get_comments(session_id)


def export_analysis_for_sharing(analysis_results: Dict) -> Dict:
    """Prepare analysis results for sharing (remove sensitive data)."""
    # Create a copy for sharing
    share_data = {
        'summary': analysis_results.get('summary', {}),
        'recommendations': analysis_results.get('recommendations', []),
        'market_context': analysis_results.get('market_context', []),
        'charts_data': {},  # Will be populated with serializable chart data
        'metadata': {
            'created_at': datetime.now().isoformat(),
            'version': '1.0',
            'shared': True
        }
    }

    # Add key metrics (without raw customer data)
    if 'comparison_df' in analysis_results:
        df = analysis_results['comparison_df']
        share_data['key_metrics'] = {
            'total_customers': len(df),
            'total_delta': float(df['DELTA'].sum()) if 'DELTA' in df.columns else 0,
            'avg_balance_change': float(df['DELTA'].mean()) if 'DELTA' in df.columns else 0,
        }

    return share_data


def render_sharing_interface(analysis_results: Dict):
    """Render the sharing interface in Streamlit."""
    st.header("📤 Chia sẻ Phân tích")

    with st.expander("Tạo liên kết chia sẻ", expanded=False):
        col1, col2 = st.columns(2)

        with col1:
            share_title = st.text_input("Tiêu đề", value="Phân tích tiền gửi")
            share_description = st.text_area("Mô tả", height=100,
                value="Phân tích so sánh tiền gửi T1/T2 với insights AI")

        with col2:
            custom_password = st.text_input("Mật khẩu tùy chỉnh (tùy chọn)",
                type="password", help="Để trống để tạo mật khẩu ngẫu nhiên")
            expiry_days = st.slider("Thời hạn (ngày)", 1, 30, 7)

        if st.button("Tạo liên kết chia sẻ", type="primary"):
            try:
                # Prepare data for sharing
                share_data = export_analysis_for_sharing(analysis_results)

                # Create shared session
                share_url, password = create_shareable_link(
                    share_data, share_title, share_description,
                    custom_password if custom_password else None, expiry_days
                )

                st.success("✅ Liên kết chia sẻ đã được tạo!")

                # Display share info
                st.code(f"URL: {share_url}")
                st.code(f"Mật khẩu: {password}")

                st.info("💡 Chia sẻ URL và mật khẩu này với đồng nghiệp để họ có thể xem phân tích của bạn.")

            except Exception as e:
                st.error(f"❌ Lỗi tạo liên kết: {str(e)}")

    # Comments section
    st.subheader("💬 Thảo luận")

    # Check if we have a session ID (from URL or stored)
    session_id = st.query_params.get("session", None) or st.session_state.get("current_session_id")

    if session_id:
        # Load comments
        comments = get_collaboration_comments(session_id)

        # Display existing comments
        if comments:
            st.write("**Bình luận:**")
            for comment in comments:
                with st.container():
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"**{comment['user_name']}** ({comment['created_at'][:19]})")
                        st.write(comment['comment'])
                    with col2:
                        pass  # Could add edit/delete buttons for comment owner
                st.divider()

        # Add new comment
        with st.form("add_comment"):
            user_name = st.text_input("Tên của bạn", value="Anonymous")
            new_comment = st.text_area("Bình luận mới", height=100)

            if st.form_submit_button("Gửi bình luận"):
                if add_collaboration_comment(session_id, user_name, new_comment):
                    st.success("✅ Bình luận đã được thêm!")
                    st.rerun()
                else:
                    st.error("❌ Không thể thêm bình luận. Vui lòng kiểm tra lại.")
    else:
        st.info("💡 Tạo liên kết chia sẻ ở trên để bắt đầu thảo luận với đồng nghiệp.")


def render_shared_analysis_viewer():
    """Render interface for viewing shared analysis."""
    st.header("👁️ Xem Phân tích Chia sẻ")

    # Get session ID from URL parameters
    session_id = st.query_params.get("session", "")
    password = st.text_input("Mật khẩu", type="password")

    if st.button("Xem phân tích"):
        if not session_id or not password:
            st.error("Vui lòng nhập đầy đủ Session ID và mật khẩu.")
            return

        shared_data = load_shared_analysis(session_id, password)

        if shared_data:
            st.success("✅ Đã tải phân tích chia sẻ!")

            # Store session ID for comments
            st.session_state.current_session_id = session_id

            # Display shared analysis
            if 'summary' in shared_data:
                st.subheader("📊 Tóm tắt")
                st.json(shared_data['summary'])

            if 'recommendations' in shared_data:
                st.subheader("💡 Khuyến nghị")
                for rec in shared_data['recommendations']:
                    st.write(f"• {rec}")

            if 'market_context' in shared_data:
                st.subheader("🌍 Bối cảnh thị trường")
                for context in shared_data['market_context']:
                    st.write(context)

            if 'key_metrics' in shared_data:
                st.subheader("📈 Chỉ số chính")
                metrics = shared_data['key_metrics']
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Tổng khách hàng", f"{metrics['total_customers']:,}")
                with col2:
                    st.metric("Tổng thay đổi", f"{metrics['total_delta']:,.0f}")
                with col3:
                    st.metric("Thay đổi TB", f"{metrics['avg_balance_change']:,.0f}")

        else:
            st.error("❌ Không thể tải phân tích. Vui lòng kiểm tra Session ID và mật khẩu.")