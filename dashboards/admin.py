import streamlit as st
import sqlite3
import pandas as pd
import controller as controller 
from datetime import datetime
from utility.generate_key import decrypt_text


conn = sqlite3.connect("hospital.db", check_same_thread=False)
c = conn.cursor()

if 'start_time' not in st.session_state:
    st.session_state.start_time = datetime.now()

uptime = datetime.now() - st.session_state.start_time

def run_admin_dashboard(username, user_id):
    # --- PAGE CONFIG ---
    st.set_page_config(page_title="Admin Dashboard", page_icon="assets/logo.png", layout="wide")

    # --- Connect to DB ---

    # --- HEADER ---
    st.markdown("<h2 style='text-align:center;color:#008080;'>ADMIN DASHBOARD</h2>", 
                unsafe_allow_html=True)
    st.write(f"Welcome, **{username}**! Manage patients, logs, and monitor hospital data.")

    # --- SIDEBAR MENU ---
    st.sidebar.markdown("<h3 style='color:#008080;'>Navigation</h3>", unsafe_allow_html=True)
    if st.button("Logout", key="logout_admin"):
        st.session_state.clear()     # removes all session stored values
        st.rerun()                   # refresh the app, sending user to login page

    menu = st.sidebar.radio(
        "Go to:",
        ["Manage Patients", "Activity Logs", "Manage Users"],
        index=0
    )

    # =====================================
    # ----------- PAGE 1 ------------------
    # =====================================
    if menu == "Manage Patients":
        tab1, tab2, tab3 = st.tabs(["View All Patients", "Add Patient", "Edit Patient"])
        with tab1:
            st.subheader("All Registered Patients")
            if controller.permission("admin", "view_patients", user_id):
                patients = controller.ViewPatients("admin", user_id)
                if (patients):
                    df_patients = pd.DataFrame(patients, columns=["patient_id", "name", "contact", "daignosis", "anonymized_name", "anonymized_contact", "date_added"])
    
                    # Display and download
                    st.dataframe(df_patients, use_container_width="stretch")
                    csv = df_patients.to_csv(index=False)
                    st.download_button("Download Logs", data=csv, file_name="patients_logs.csv")
                else: 
                    print("No patients found")

        with tab2:
            st.subheader("Add New Patient")
            if controller.permission("admin", "add_patients" ,user_id):
                with st.form("add_patient_form"):
                    new_name = st.text_input("Name")
                    new_contact = st.text_input("Contact")
                    new_diagnosis = st.text_input("Diagnosis")

                    submit_add = st.form_submit_button("Create Patient")

                if submit_add:
                    controller.Add_Patient(user_id, "admin", patient_name=new_name, patient_contact=new_contact, patient_diagnosis=new_diagnosis)       
                    st.rerun()

        with tab3:
            patients = c.execute("SELECT * FROM patients").fetchall()
            columns = [desc[0] for desc in c.description]
            decrypted_rows = []

            for row in patients:
                row = list(row)  # convert tuple → list so we can modify

               # Assuming DB columns: (patient_id, name, contact_encrypted, diagnosis, anonymized_name, anonymized_contact, ...)
                contact_encrypted = row[2]

                try:
                    row[2] = decrypt_text(contact_encrypted)
                except:
                    row[2] = "DECRYPTION ERROR"

                decrypted_rows.append(tuple(row))

            patients = decrypted_rows
            df_patients = pd.DataFrame(patients, columns=columns)

            if not df_patients.empty:
                # Let admin select patient
                selected_id = st.selectbox("Select Patient to Edit", df_patients['patient_id'])
                selected_patient = df_patients[df_patients['patient_id'] == selected_id].iloc[0]

                # Edit form
                if controller.permission("admin", "edit_patients", user_id):

                    with st.form(key=f"edit_form_{selected_id}"):
                        new_name = st.text_input("Name", value=selected_patient['name'])
                        new_contact = st.text_input("Contact", value=selected_patient['contact'])
                        new_diagnosis = st.text_input("Diagnosis", value=selected_patient['diagnosis'])
                        submit_edit = st.form_submit_button("Update Patient")

                        if submit_edit:
                            controller.Edit_Patient(user_id, "admin", patient_id=selected_id, new_name=new_name, new_contact=new_contact, new_diagnosis=new_diagnosis, original_patient=selected_patient)
                            st.rerun()

                # Optional Delete Button
                if controller.permission("admin", "delete_patients", user_id):
                    with st.form(key=f"delete_form_{selected_id}"):
                        st.write("### Delete Patient")
                        confirm = st.checkbox("Are you sure you want to delete this patient?")
                        delete_btn = st.form_submit_button("Delete Patient")

                        if delete_btn:
                            if confirm:
                                controller.Delete_Patient(user_id, "admin", selected_id)
                                st.rerun()
                            else:
                                st.warning("Please check the confirmation box before deleting.")

            else:
                st.info("No patients to edit.")

        c.execute("SELECT MAX(date_added) FROM patients")
        last_sync = c.fetchone()[0]

    # =====================================
    # ----------- PAGE 2 ------------------
    # =====================================
    elif menu == "Activity Logs":

        tab1, tab2 = st.tabs(["User Activity Logs", "Activity Graphs"])

        df_logs = None   # <-- IMPORTANT: define before tabs

        with tab1:
            st.subheader("User Activity Logs")

            df_logs = None  # Make df_logs available to both tabs

            if controller.permission("admin", "view_logs", user_id):
                logs = controller.View_User_logs(user_id, "admin")

                if logs:
                    df_logs = pd.DataFrame(logs, columns=[
                    "log_id", "user_id", "role", "action", "timestamp", "details"
                    ])

                    st.dataframe(df_logs, width="stretch")

                    st.download_button(
                    "Download Logs",
                    data=df_logs.to_csv(index=False),
                    file_name="audit_logs.csv"
                    )
                else:
                    st.info("No logs found yet.")

        with tab2:
            st.subheader("Activity Graphs")

            if df_logs is None or df_logs.empty:
                st.warning("No data available for graphs yet.")
            else:
                # Convert timestamp to date
                df_logs["date"] = pd.to_datetime(df_logs["timestamp"]).dt.date

                # User filter
                users = ["ALL"] + sorted(df_logs["user_id"].unique().tolist())
                selected_user = st.selectbox("Filter by user:", users)

                df = df_logs.copy()

                if selected_user != "ALL":
                    df = df[df["user_id"] == selected_user]

                # Group by date
                activity = df.groupby("date").size().reset_index(name="actions")

                st.bar_chart(activity.set_index("date"))


        # Last sync safely
        c.execute("SELECT MAX(timestamp) FROM logs")
        row = c.fetchone()
        last_sync = row[0] if row and row[0] else "No logs yet"
    
    elif menu == "Manage Users":
        if controller.permission("admin", "manage_users", user_id ):
            tab1, tab2 = st.tabs(["View Users", "Add Users"])

            with tab1: 
                st.subheader("All Users")
                users = controller.ViewUsers("admin", user_id)
                if (users):
                    df_users = pd.DataFrame(users, columns=["user_id", "username", "role", "password"])
    
                    # Display and download
                    st.dataframe(df_users, use_container_width="stretch")
                    csv = df_users.to_csv(index=False)
                    st.download_button("Download Logs", data=csv, file_name="users_logs.csv")
                else: 
                    print("No users found")
            
            with tab2:
                st.subheader("Add New User")
                if controller.permission("admin", "manage_users" ,user_id):
                    with st.form("add_user_form"):
                        new_username = st.text_input("Username")
                        new_password = st.text_input("Password")
                        new_role = st.text_input("Role")

                        submit_add = st.form_submit_button("Create User")

                    if submit_add:
                       controller.Add_User(user_id, "admin", new_username, new_password, new_role)       
                       st.rerun()
    
        c.execute("SELECT MAX(timestamp) FROM logs WHERE user_id = ?", (user_id,))
        row = c.fetchone()
        last_sync = row[0] if row and row[0] else "No users yet"
    



    
    st.markdown(f"<footer style='text-align:center;color:gray;'>Uptime: {uptime} | Last Sync: {last_sync}</footer>", unsafe_allow_html=True)
