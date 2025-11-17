import streamlit as st
from login import login_user
import dashboards.admin as admin
import dashboards.doctor as doctor
import dashboards.receptionist as recep
import utility.log as log

log.clean_old_data()

st.set_page_config(page_title="Hospital Management", page_icon="assets/logo.png", layout="wide")

# -------------------------------- CSS --------------------------------
st.markdown("""
<style>

.main > div { padding-top: 0rem; }
            
.full-wrapper {
    display: flex;
    flex-direction: row;
    width: 100%;
    height: 100vh;
}

/* Left section */
.left-half {
    flex: 1;
    background-color: #007f7f;
    padding: 4rem 2rem;
    color: white;
    border-radius: 0 20px 20px 0;
}

/* Right section */
.right-half {
    flex: 1;
    background-color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 4rem 2rem;
}

/* Login card */
.login-container {
    width: 360px;
    background: rgba(255, 255, 255, 0.15);
    padding: 2rem;
    border-radius: 16px;
    box-shadow: 0 4px 20px rgba(0, 128, 128, 0.2);
    backdrop-filter: blur(10px);
}


/* Input styling */
.stTextInput > div > div > input { 
    background: transparent;
    color: #004D4D; 
    border: none; 
    border-bottom: 2px solid #008080; 
    border-radius: 0;
    padding: 10px 0; 
    font-size: 1rem; 
}
.stTextInput > div > div > input:focus { 
    border-bottom: 2px solid #20B2AA; 
    box-shadow: 0 4px 8px -4px rgba(32, 178, 170, 0.4); 
    outline: none; 
}

/* Label */
.stTextInput label { 
    color: #00796B !important; 
    font-weight: 600; 
}

/* Button */
.stButton > button { 
    background-color: #008080; 
    color: white; 
    font-weight: 600; 
    border: none; 
    border-radius: 8px; 
    padding: 0.6em 2em; 
    font-size: 1rem;
    box-shadow: 0 0 12px rgba(0, 128, 128, 0.4); 
    position: relative; 
}
.stButton > button::after {
    content: ""; 
    position: absolute; 
    bottom: -6px; 
    left: 50%; 
    transform: translateX(-50%); 
    width: 60%; 
    height: 8px; 
    border-radius: 50%; 
    background: rgba(0, 128, 128, 0.6); 
    filter: blur(6px); 
}
.stButton > button:hover { 
    background-color: #20B2AA; 
    transform: translateY(-2px); 
}
.stButton > button:hover::after { 
    width: 80%; 
    background: rgba(32, 178, 170, 0.8); 
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------

left, right = st.columns([1, 1])

# Initialize session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.user_id = None
    st.session_state.username = ""

# --- GDPR Consent Banner ---
if "gdpr_consent" not in st.session_state:
    st.session_state.gdpr_consent = False

if not st.session_state.gdpr_consent:
    st.warning(
        "This site collects and processes patient data. "
        "Please consent to data collection for full functionality."
    )
    consent = st.checkbox("I consent to the use of my data according to GDPR guidelines")
    if consent:
        st.session_state.gdpr_consent = True
    else:
        st.stop()

# ------------------------- LOGIN PAGE -------------------------
if not st.session_state.logged_in:

    with left:
        st.markdown("""
        <div class="full-wrapper">
        <div class="left-half">
            <h1 style='font-size: 3rem; font-weight: bold;'>HEALTH NET SYSTEMS</h1>
            <p style='font-size: 1.2rem;'>Your trusted hospital management suite.</p>
        </div>
        </div>            
        """, unsafe_allow_html=True)

    with right:
        st.markdown("<div class='right-half'>", unsafe_allow_html=True)

        st.markdown("<h2 style='text-align:center;color:#008080;'>LOGIN</h2>", unsafe_allow_html=True)
        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="password")

        login_btn = st.button("Login")

        if login_btn:
            role, user_id = login_user(username, password)
            if role:
                st.session_state.logged_in = True
                st.session_state.role = role
                st.session_state.username = username
                st.session_state.user_id = user_id
                log.log_action(user_id, role, "login", "User logged in")
                st.rerun()
            else:
                st.error("❌ Invalid username or password")

        st.markdown("</div>", unsafe_allow_html=True)

# --------------------- ROLE REDIRECTION ----------------------
if st.session_state.logged_in:

    if st.session_state.role == "admin":
        admin.run_admin_dashboard(st.session_state.username, st.session_state.user_id)
    elif st.session_state.role == "doctor":
        doctor.run_doctor_dashboard(st.session_state.username, st.session_state.user_id)
    elif st.session_state.role == "receptionist":
        recep.run_reception_dashboard(st.session_state.username, st.session_state.user_id)
