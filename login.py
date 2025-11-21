import sqlite3
import hashlib
import streamlit as st
import utility.log as log

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def login_user(username, password):
    try:
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
    except sqlite3.Error as e:
        st.error("Error loging in.")
        log.log_action(user_id, role, "error", f"ViewPermissions failed: {e}")

