import streamlit as st
import sqlite3
import utility.log as log
import utility.anonymize_data as anonymize
from utility.generate_key import encrypt_text, decrypt_text
from login import hash_password

conn = sqlite3.connect("hospital.db", check_same_thread=False)
c = conn.cursor()

def permission(role, function, user_id):
    c.execute("""
    SELECT permission 
    FROM roles_permissions 
    WHERE role = ?
    """, (role,))
    allowed_actions = [row[0] for row in c.fetchall()]
    if function not in allowed_actions:
        log.log_action(user_id, role, "unauthorized_attempt", f"Tried to {function}")
        return False
    return True

def ViewPatients(role, user_id):
    if not permission(role, "view_patients", user_id):
        st.error("Unauthorized")
        st.stop()

    # --- ADMIN: Full access, decrypt contact ---
    if role == "admin":
        rows = c.execute("SELECT * FROM patients").fetchall()
        decrypted_rows = []

        for row in rows:
            row = list(row)  # convert tuple → list so we can modify

            # Assuming DB columns: (patient_id, name, contact_encrypted, diagnosis, anonymized_name, anonymized_contact, ...)
            contact_encrypted = row[2]
            print(f"Raw DB value: {contact_encrypted}")  # check what’s stored

            try:
                row[2] = decrypt_text(contact_encrypted)
            except Exception as e:
                print(f"Decryption failed for patient_id={row[0]}: {e}")
                row[2] = "DECRYPTION ERROR"

            decrypted_rows.append(tuple(row))

        patients = decrypted_rows

    # --- DOCTOR: Anonymized only ---
    elif role == "doctor":
        patients = c.execute(
            "SELECT anonymized_name, anonymized_contact, diagnosis FROM patients"
        ).fetchall()

    # --- RECEPTIONIST or INVALID ROLE ---
    else:
        patients = []

    # Log the action once
    log.log_action(user_id, role, "view_patients", f"Viewed {len(patients)} patients")

    return patients


def Add_Patient(user_id, role, patient_name, patient_contact, patient_diagnosis):
    # Check permission
    if not permission(role, "add_patients", user_id):
        st.error("Unauthorized")
        st.stop()

    if patient_name and patient_contact and patient_diagnosis:
        # Generate anonymized data
        anonymize_name = anonymize.generate_anonymized_name(patient_name)
        anonymize_contact = anonymize.generate_masked_contact(patient_contact)
        encrypted_contact = encrypt_text(patient_contact)

        # Insert into DB
        c.execute(
            """
            INSERT INTO patients 
            (name, contact, diagnosis, anonymized_name, anonymized_contact) 
            VALUES (?, ?, ?, ?, ?)
            """,
            (patient_name, encrypted_contact, patient_diagnosis, anonymize_name, anonymize_contact)
        )
        conn.commit()

        # Get the new patient_id
        patient_id = c.lastrowid

        st.success(f"✅ Patient '{patient_name}' added successfully!")
        # Log action with patient_id
        log.log_action(user_id, role, "add_patient", f"Added patient ID={patient_id}, current name={patient_name}")
        log.log_action(user_id, role, "anonymization", f"Anonymized patient ID={patient_id}, current name={anonymize_name}"
)
    else:
        st.warning("Please fill in all fields.")

def Edit_Patient(user_id, role, patient_id, new_name, new_contact, new_diagnosis, original_patient):
    if not permission(role, "edit_patients", user_id):
        st.error("Unauthorized")
        st.stop()

    # ============================
    #        ADMIN SECTION
    # ============================
    if role == "admin":

        # Compare with original values
        name_changed = new_name != original_patient['name']
        contact_changed = new_contact != original_patient['contact']
        # Recompute anonymized name if changed
        if name_changed:
            anonymize_name = anonymize.generate_anonymized_name(new_name)
            log.log_action(user_id, role, "anonymization",
                           f"Anonymized patient ID={patient_id}, new name='{new_name}'")
        else:
            anonymize_name = original_patient['anonymized_name']

        # Recompute anonymized contact & encrypt if changed
        if contact_changed:
            anonymize_contact = anonymize.generate_masked_contact(new_contact)
            encrypted_contact = encrypt_text(new_contact)

            log.log_action(user_id, role, "anonymization",
                           f"Anonymized patient ID={patient_id}, contact updated")
        else:
            anonymize_contact = original_patient['anonymized_contact']
            encrypted_contact = encrypt_text(original_patient['contact'])
    # Update DB
        c.execute("""
            UPDATE patients
            SET name = ?, contact = ?, diagnosis = ?, anonymized_name = ?, anonymized_contact = ?
            WHERE patient_id = ?
        """, (new_name, encrypted_contact, new_diagnosis, anonymize_name, anonymize_contact, patient_id))

        conn.commit()
        log.log_action(user_id, role, "update_patient", f"Updated patient ID={patient_id}")

    # ============================
    #        DOCTOR SECTION
    # ============================
    elif role == "doctor":
        # Doctor can ONLY change diagnosis
        if new_diagnosis != original_patient.diagnosis:
            c.execute("""
            UPDATE patients
            SET diagnosis = ?
            WHERE patient_id = ?
        """, (new_diagnosis, patient_id))

            conn.commit()
            log.log_action(user_id, role, "update_patient",
                       f"Doctor updated diagnosis for patient ID={patient_id}")

            st.success("Patient updated successfully!")

def Delete_Patient(user_id, role, patient_id):
    if not permission(role, "delete_patients", user_id):
        st.error("Unauthorized")
        st.stop()
    c.execute("DELETE FROM patients WHERE patient_id = ?", (patient_id,))
    conn.commit()
    st.warning(f"Patient ID {patient_id} deleted!")
    log.log_action(user_id, "admin", "delete_patient", f"Deleted patient ID={patient_id}")

def View_User_logs(user_id, role):
    if not permission(role, "view_logs", user_id):
        st.error("Unauthorized")
        st.stop()
    
    logs = c.execute("SELECT * FROM logs ORDER BY timestamp DESC").fetchall()
    
    log.log_action(user_id, role , "view_logs", f"Viewd all logs")
    return logs


def ViewUsers(role, user_id):
    if not permission(role, "manage_users", user_id ):
        st.error("Unauthorized")
        st.stop()
    elif role == "admin":
        users = c.execute("SELECT user_id, username, role, password FROM users").fetchall()
    else:
        users = []

    # Log the action once
    log.log_action(user_id, role, "manage_users", f"Viewed {len(users)} users")

    return users

def Add_User(user_id, role, username, password, new_role):
    # Check permission
    if not permission(role, "manage_users", user_id):
        st.error("Unauthorized")
        st.stop()

    if username and password and new_role:
        # Generate anonymized data
        hased_password = hash_password(password)
        # Insert into DB
        c.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            (username, hased_password, new_role)
        )
        conn.commit()

        # Get the new patient_id
        user_id = c.lastrowid

        st.success(f"✅ User '{username}' added successfully!")
        # Log action with patient_id
        log.log_action(user_id, role, "manage_users", f"Added user ID={user_id}")
    else:
        st.warning("Please fill in all fields.")

def Edit_User(editor_id, editor_role, target_user_id, new_username, new_password, new_role, original_user):
    """
    editor_id      → the ID of the logged-in user making changes
    editor_role    → role of logged-in user (admin)
    target_user_id → the user being edited
    new_*          → new values submitted from the form
    original_user  → original row fetched from DB
    """

    # Permission check
    if not permission(editor_role, "manage_users", editor_id):
        st.error("Unauthorized")
        st.stop()

    # Admin cannot change their own role (security rule)
    if target_user_id == editor_id and new_role != original_user["role"]:
        st.error("You cannot change your own role.")
        st.stop()

    changes = []  # For logging

    # ============================
    #      FIELD-BY-FIELD EDIT
    # ============================

    # 1. Username change
    if new_username != original_user["username"]:
        c.execute("UPDATE users SET username=? WHERE user_id=?",
                  (new_username, target_user_id))
        changes.append(f"username: {original_user['username']} → {new_username}")

    # 2. Role change (admin only)
    if new_role != original_user["role"]:
        c.execute("UPDATE users SET role=? WHERE user_id=?",
                  (new_role, target_user_id))
        changes.append(f"role: {original_user['role']} → {new_role}")

    # 3. Password change (only if provided)
    if new_password.strip() != "":
        hashed_pw = hash_password(new_password)
        c.execute("UPDATE users SET password=? WHERE user_id=?",
                  (hashed_pw, target_user_id))
        changes.append("password: updated")

    # Commit if anything changed
    if changes:
        conn.commit()
        change_text = "; ".join(changes)
        log.log_action(editor_id, editor_role, "edit_user",
                       f"Edited user_id={target_user_id}: {change_text}")
        st.success("User updated successfully!")
    else:
        st.info("No changes made.")
