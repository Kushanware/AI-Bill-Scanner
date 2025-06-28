import streamlit as st
import streamlit_oauth
from ocr_utils import extract_text_from_image, parse_bill_text
from model import load_model_and_vectorizer, predict_category
from tips import generate_tips
from db_utils import create_table, save_scan, fetch_user_scans
import re
import os
from datetime import datetime
from streamlit_oauth import OAuth2Component

# --- GitHub OAuth Credentials (hardcoded) ---
GITHUB_CLIENT_ID = "Ov23liXdCJTnZDqEdqLp"
GITHUB_CLIENT_SECRET = "b78e8820f11bfc7402978c9aa33d3c85b94319d2"

# Set page config
st.set_page_config(page_title="SmartBill Scanner", page_icon="📷", layout="centered")

def add_header_logo():
    st.markdown(
        """
        <div style='text-align: center;'>
            <img src='https://cdn-icons-png.flaticon.com/512/2920/2920244.png' width='100'/>
        </div>
        """,
        unsafe_allow_html=True
    )
add_header_logo()

st.title("📷 SmartBill Scanner")
st.markdown("""
A modern, AI-powered bill/receipt scanner that extracts, categorizes, and helps you save on your expenses!
""")

# Sidebar for navigation and info
with st.sidebar:
    st.header("Navigation")
    st.markdown("- [Upload Bill](#upload-your-bill)")
    st.markdown("- [Scan History](#your-scan-history)")
    st.markdown("---")
    st.info("Developed by [Your Name]")
    st.markdown("---")
    st.write("**How it works:** Upload a bill, get instant insights, and track your spending history.")

# Create DB table if not exists
create_table()

# --- GitHub OAuth Login ---
user_name = None
user_email = None
is_authenticated = False

# Initialize the component
oauth2 = OAuth2Component(
    client_id=GITHUB_CLIENT_ID,
    client_secret=GITHUB_CLIENT_SECRET,
    authorize_endpoint="https://github.com/login/oauth/authorize",
    token_endpoint="https://github.com/login/oauth/access_token",
)

# Call the component in your Streamlit app
result = oauth2.authorize_button(
    name="Login with GitHub",
    redirect_uri="http://localhost:8501/",
    scope="user:email",
    key="github"
)

if result and "token" in result:
    # Use the access token to get user info
    access_token = result["token"]["access_token"]
    import requests
    headers = {"Authorization": f"token {access_token}"}
    resp = requests.get("https://api.github.com/user", headers=headers)
    if resp.ok:
        user_info = resp.json()
        user_email = user_info.get("email", "")
        user_name = user_info.get("login", "GitHub User")
        is_authenticated = True

if is_authenticated:
    st.sidebar.success(f"Welcome, {user_name}!")
    st.sidebar.title("SmartBill Scanner")
    st.sidebar.info("Upload your bill and get instant results!")

    st.title("SmartBill Scanner")
    st.header("Upload Your Bill")

    api_key = "K86392130988957"
    current_user_id = user_name

    if "history" not in st.session_state:
        st.session_state["history"] = []

    uploaded_file = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"])
    if uploaded_file is not None:
        text = extract_text_from_image(uploaded_file, api_key)
        items, total, date = parse_bill_text(text)
        st.session_state["history"].append({"date": date, "total": total, "items": items, "text": text})

        st.markdown("---")
        st.subheader("Extracted Text:")
        st.write(text)

        st.markdown("---")
        st.subheader("Parsed Bill Data")
        st.write(f"**Date:** {date}")
        st.write(f"**Total:** {total}")
        st.write("**Items:**")
        for item in items:
            st.write(f"- {item}")

        st.markdown("---")
        st.subheader("🏷️ Predicted Categories:")
        spending = {}
        model, vectorizer = load_model_and_vectorizer()
        for item, amount in items:
            cat = predict_category(item, model, vectorizer)
            st.write(f"<b>{item}</b> → <span style='color: #2b9348;'>{cat}</span>", unsafe_allow_html=True)
            spending[cat] = spending.get(cat, 0) + amount

        st.markdown("---")
        st.subheader("💡 Smart Tips:")
        tips = generate_tips(spending)
        for tip in tips:
            st.success(tip)

        # Save scan to DB
        save_scan(current_user_id, items, total, spending)

    st.markdown("---")
    st.header("Your Scan History")
    scans = fetch_user_scans(current_user_id)
    if scans:
        for scan in scans[::-1]:  # Show latest first
            st.write(f"**Date:** {scan[2]} | **Total:** ₹{scan[4]}")
            st.json(__import__('json').loads(scan[3]))  # items
            st.markdown("---")
    else:
        st.info("No scans yet. Upload a bill to get started!")

    st.info("Tip: On your phone, tap 'Upload' and select 'Camera' to take a live photo of your bill.")

    if st.session_state["history"]:
        st.markdown("---")
        st.subheader("Scan History (this session)")
        for i, entry in enumerate(st.session_state["history"], 1):
            st.write(f"**Scan {i}:** Date: {entry['date']}, Total: {entry['total']}")
            st.write("Items:")
            for item in entry["items"]:
                st.write(f"- {item}")
            st.write("Text:")
            st.write(entry["text"])
            st.markdown("---")
else:
    st.warning("Please log in with GitHub to use the app.") 