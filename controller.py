import streamlit as st
import sqlite3
import utility.log as log
import utility.anonymize_data as anonymize
from utility.generate_key import encrypt_text, decrypt_text
from login import hash_password

conn = sqlite3.connect("hospital.db", check_same_thread=False)
c = conn.cursor()

def permission(role, function, user_id):
    try:
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
    except sqlite3.Error as e:
        st.error("Error retrieving permissions.")
        log.log_action(user_id, role, "error", f"Permissions failed: {e}")



def ViewPatients(role, user_id):
    if not permission(role, "view_patients", user_id):
        st.error("Unauthorized")
        st.stop()
    try:
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
        log.log_action(user_id, role, "view_patients", f"Viewed {len(patients)} patients")
        return patients

    except sqlite3.Error as e: 
        st.error("Error viewing paitients.")
        log.log_action(user_id, role, "error", f"View_patients failed: {e}")


def Add_Patient(user_id, role, patient_name, patient_contact, patient_diagnosis):
    # Check permission
    if not permission(role, "add_patients", user_id):
        st.error("Unauthorized")
        st.stop()
    try:
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
            log.log_action(user_id, role, "anonymization", f"Anonymized patient ID={patient_id}, current name={anonymize_name}")
        else:
            st.warning("Please fill in all fields.")
        
    except sqlite3.Error as e:
        st.error("Error adding paitient.")
        log.log_action(user_id, role, "error", f"Add_patients failed: {e}")

def Edit_Patient(user_id, role, patient_id, new_name, new_contact, new_diagnosis, original_patient):
    if not permission(role, "edit_patients", user_id):
        st.error("Unauthorized")
        st.stop()
    try:
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

                log.log_action(user_id, role, "anonymization", f"Anonymized patient ID={patient_id}, contact updated")
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

    
        elif role == "doctor":
            # Doctor can ONLY change diagnosis
            if new_diagnosis != original_patient.diagnosis:
                c.execute("""
                UPDATE patients
                SET diagnosis = ?
                WHERE patient_id = ?
            """, (new_diagnosis, patient_id))

                conn.commit()
                log.log_action(user_id, role, "update_patient", f"Doctor updated diagnosis for patient ID={patient_id}")

                st.success("Patient updated successfully!")
        else: 
            st.warning("Error occured while updating")
    except sqlite3.Error as e:
        st.error("Error editing paitient.")
        log.log_action(user_id, role, "error", f"Editing_patients failed: {e}")
        

def Delete_Patient(user_id, role, patient_id):
    if not permission(role, "delete_patients", user_id):
        st.error("Unauthorized")
        st.stop()
    try:
        c.execute("DELETE FROM patients WHERE patient_id = ?", (patient_id,))
        conn.commit()
        st.warning(f"Patient ID {patient_id} deleted!")
        log.log_action(user_id, "admin", "delete_patient", f"Deleted patient ID={patient_id}")
    except sqlite3.Error as e:
        st.error("Error deleting paitient.")
        log.log_action(user_id, role, "error", f"Deleting_patients failed: {e}")

def View_User_logs(user_id, role):
    if not permission(role, "view_logs", user_id):
        st.error("Unauthorized")
        st.stop()
    try:
        logs = c.execute("SELECT * FROM logs ORDER BY timestamp DESC").fetchall()
    
        log.log_action(user_id, role , "view_logs", f"Viewd all logs")
        return logs
    except sqlite3.Error as e:
        st.error("Error viewing user logs.")
        log.log_action(user_id, role, "error", f"View_User_logs failed: {e}")


def ViewUsers(role, user_id):
    if not permission(role, "manage_users", user_id ):
        st.error("Unauthorized")
        st.stop()
    try:
        if role == "admin":
            users = c.execute("SELECT user_id, username, role, password FROM users").fetchall()        

            # Log the action once
            log.log_action(user_id, role, "manage_users", f"Viewed {len(users)} users")

            return users
        else:
            st.warning("Unable to view users")
    except sqlite3.Error as e:
        st.error("Error viewing users.")
        log.log_action(user_id, role, "error", f"View_Users failed: {e}")

def Add_User(user_id, role, username, password, new_role):
    # Check permission
    if not permission(role, "manage_users", user_id):
        st.error("Unauthorized")
        st.stop()
    try: 
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
    except sqlite3.Error as e:
        st.error("Error adding user.")
        log.log_action(user_id, role, "error", f"Add_user failed: {e}")
