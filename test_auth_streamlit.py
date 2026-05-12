#!/usr/bin/env python3
"""Simple test to verify Streamlit + auth integration"""

import streamlit as st
from auth_manager import authenticate_user

st.set_page_config(page_title="Auth Test", layout="wide")

st.title("🔐 Authentication Test")

# Test 1: Check if session state works
st.subheader("Test 1: Session State")
if 'test_logged_in' not in st.session_state:
    st.session_state['test_logged_in'] = False

st.write(f"Session state initialized: {st.session_state['test_logged_in']}")

# Test 2: Manual login form
st.subheader("Test 2: Direct Authentication")

with st.form("test_auth"):
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    submit = st.form_submit_button("Test Auth")
    
    if submit:
        st.write(f"Testing: {username} / {password}")
        result = authenticate_user(username, password)
        if result:
            st.success(f"✅ Auth Success! User: {result['full_name']}")
        else:
            st.error("❌ Auth Failed!")

# Test 3: List users
st.subheader("Test 3: Available Users")
from auth_manager import list_all_users

users = list_all_users()
if users:
    st.write("Users in database:")
    for user in users:
        st.write(f"  - {user['username']} ({user['role']})")
else:
    st.error("No users found!")
