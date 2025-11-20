import sqlite3
import hashlib
import streamlit as st

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def login_user(username, password):
    conn = sqlite3.connect("hospital.db")
    c = conn.cursor()
    hashed = hash_password(password)
    c.execute("SELECT role, user_id FROM users WHERE username=? AND password=?", (username, hashed))
    data = c.fetchone()
    conn.close()
    if data:
        role = data[0].lower()  # role
        user_id = data[1] 
        return role, user_id
    else: 
        st.warning("Login failed")


def has_permission(role, permission):
    conn = sqlite3.connect("hospital.db")
    c = conn.cursor()
    c.execute("SELECT 1 FROM roles_permissions WHERE role=? AND permission=?", (role, permission))
    result = c.fetchone()
    conn.close()
    return bool(result)
