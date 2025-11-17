# dashboards/doctor.py
import streamlit as st
import sqlite3
from datetime import datetime
import controller
import pandas as pd
import utility.log as log

if 'start_time' not in st.session_state:
    st.session_state.start_time = datetime.now()

uptime = datetime.now() - st.session_state.start_time

def run_reception_dashboard(username, user_id):
    """Run the Receptionist Dashboard for the logged-in user"""
    
    # --- Page Config ---
    st.set_page_config(page_title="Receptionist Dashboard", page_icon="assets/logo.png", layout="wide")

    # --- Header ---
    st.markdown("<h2 style='text-align:center;color:#008080;'>RECEPTIONIST DASHBOARD</h2>", unsafe_allow_html=True)
    st.write(f"Welcome **{username}**! Here you can view and manage patients.")

    # --- Connect to DB ---
    conn = sqlite3.connect("hospital.db")
    c = conn.cursor()
    st.sidebar.markdown("<h3 style='color:#008080;'>Navigation</h3>", unsafe_allow_html=True)
    if st.button("Logout", key="logout_receptionist"):
        st.session_state.clear()     # removes all session stored values
        st.rerun()                   # refresh the app, sending user to login page

    menu = st.sidebar.radio(
        "Go to:",
        ["Manage Patients", "Activity Logs"],
        index=0
    )
    if menu == "Manage Patients":

        tab1, tab2 = st.tabs(["Add Patient", "Edit Patient"])
    
        with tab1:
            st.subheader("Add New Patient")
            if controller.permission("receptionist", "add_patients" ,user_id):
                with st.form("add_patient_form"):
                    new_name = st.text_input("Name")
                    new_contact = st.text_input("Contact")
                    new_diagnosis = st.text_input("Diagnosis")

                    submit_add = st.form_submit_button("Create Patient")

                if submit_add:
                    controller.Add_Patient(user_id, "receptionist", patient_name=new_name, patient_contact=new_contact, patient_diagnosis=new_diagnosis)       
                    st.rerun()

            with tab2:
                st.subheader("Edit Patient")
                if controller.permission("doctor", "edit_patients", user_id):
                    st.warning("Cannot edit as only daignosis and user personal details provided in table")
                else: 
                    st.warning("Unauthorized")

        c.execute("SELECT MAX(date_added) FROM patients")
        last_sync = c.fetchone()[0]

    elif menu == "Activity Logs":
        tab1, tab2 = st.tabs(["User Activity Logs", "Activity Graphs"])
        df_logs = None

        with tab1:
            st.subheader("User Activity Logs")
        # Correct SQL
            logs = c.execute("SELECT * FROM logs WHERE user_id = ? ORDER BY timestamp DESC", (user_id,)).fetchall()
            conn.commit()
            log.log_action(user_id, "doctor", "view_logs", "Viewed own logs")

            if logs:
                df_logs = pd.DataFrame(logs, columns=["log_id", "user_id", "role", "action", "timestamp", "details"])
                st.dataframe(df_logs, use_container_width=True)
                st.download_button("Download Logs", data=df_logs.to_csv(index=False), file_name="audit_logs.csv")
            else:
                st.info("No logs found yet.")

        with tab2: 
            st.subheader("Activity Graphs")
            if df_logs is None or df_logs.empty:
                st.warning("No data available for graphs yet.")
            else:
                df_logs["date"] = pd.to_datetime(df_logs["timestamp"]).dt.date
                activity = df_logs.groupby("date").size().reset_index(name="actions")
                st.bar_chart(activity.set_index("date"))

        c.execute("SELECT MAX(timestamp) FROM logs")
        row = c.fetchone()
        last_sync = row[0] if row and row[0] else "No logs yet"

    st.markdown(f"<footer style='text-align:center;color:gray;'>Uptime: {uptime} | Last Sync: {last_sync}</footer>", unsafe_allow_html=True)