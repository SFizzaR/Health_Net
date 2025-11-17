import sqlite3
import hashlib
from datetime import datetime

# ----------------------------
# --- Helper Functions ---
# ----------------------------
def hash_password(password: str) -> str:
    """Return SHA-256 hash of a password."""
    return hashlib.sha256(password.encode()).hexdigest()

# ----------------------------
# --- Connect to DB ---
# ----------------------------
conn = sqlite3.connect("hospital.db")
cursor = conn.cursor()

# ----------------------------
# --- USERS TABLE ---
# ----------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT NOT NULL,
    FOREIGN KEY(role) REFERENCES roles(role)
)
""")

# ----------------------------
# --- ROLES TABLE ---
# ----------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS roles (
    role TEXT PRIMARY KEY
)
""")


# ----------------------------
# --- PERMISSIONS TABLE ---
# ----------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS permissions (
    permission TEXT PRIMARY KEY
)
""")

# ----------------------------
# --- ROLES_PERMISSIONS TABLE ---
# ----------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS roles_permissions (
    role TEXT,
    permission TEXT,
    PRIMARY KEY(role, permission),
    FOREIGN KEY(role) REFERENCES roles(role),
    FOREIGN KEY(permission) REFERENCES permissions(permission)
)
""")

# ----------------------------
# --- PATIENTS TABLE ---
# ----------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS patients (
    patient_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    contact TEXT,
    diagnosis TEXT,
    anonymized_name TEXT,
    anonymized_contact TEXT,
    date_added DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

# ----------------------------
# --- LOGS TABLE ---
# ----------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS logs (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    role TEXT,
    action TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    details TEXT,
    FOREIGN KEY(user_id) REFERENCES users(user_id)
)
""")

# ----------------------------
# --- INSERT DEFAULT ROLES ---
# ----------------------------
roles = ["admin", "doctor", "receptionist"]
for r in roles:
    try:
        cursor.execute("INSERT INTO roles (role) VALUES (?)", (r,))
    except sqlite3.IntegrityError:
        pass  # Already exists

# ----------------------------
# --- INSERT DEFAULT PERMISSIONS ---
# ----------------------------
permissions = [
    "view_patients",
    "edit_patients",
    "add_patients",
    "delete_patients",
    "manage_users",
    "view_logs"
]
for p in permissions:
    try:
        cursor.execute("INSERT INTO permissions (permission) VALUES (?)", (p,))
    except sqlite3.IntegrityError:
        pass

# ----------------------------
# --- ASSIGN PERMISSIONS TO ROLES ---
# ----------------------------
roles_permissions_map = {
    "admin": permissions,  # Admin has all permissions
    "doctor": ["view_patients", "edit_patients", "add_patients"],
    "receptionist": ["view_patients", "add_patients"]
}

for role, perms in roles_permissions_map.items():
    for perm in perms:
        try:
            cursor.execute(
                "INSERT INTO roles_permissions (role, permission) VALUES (?, ?)",
                (role, perm)
            )
        except sqlite3.IntegrityError:
            pass

# ----------------------------
# --- INSERT DEFAULT USERS ---
# ----------------------------
default_users = [
    ("admin", "admin123", "admin"),
    ("Dr. Bob", "doc123", "doctor"),
    ("Alice_recep", "rec123", "receptionist")
]

for username, password, role in default_users:
    try:
        hashed = hash_password(password)
        cursor.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            (username, hashed, role)
        )
    except sqlite3.IntegrityError:
        pass  # User already exists

# ----------------------------
# --- Commit & Close DB ---
# ----------------------------
conn.commit()
conn.close()

print("✅ Database setup complete! Users, roles, permissions, patients, and logs created.")
