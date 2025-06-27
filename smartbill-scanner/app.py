import streamlit as st
import streamlit_authenticator as stauth
from ocr_utils import extract_text_from_image, parse_bill_text
from model import load_model_and_vectorizer, predict_category
from tips import generate_tips
from db_utils import create_table, save_scan, fetch_user_scans
import re
import base64
import os
from datetime import datetime

# Helper: Improved extract_fields with skip logic
def extract_fields(text):
    items = []
    total = 0
    date = re.findall(r'\d{2}/\d{2}/\d{4}', text)
    lines = text.split('\n')
    skip_keywords = ['gst', 'sgst', 'cgst', 'igst', 'tax', 'total', 'packing', 'delivery']
    for line in lines:
        if any(char.isdigit() for char in line):
            if any(kw in line.lower() for kw in skip_keywords):
                continue  # Skip tax and service lines
            match = re.search(r'(.*?)(\d+\.\d{2})', line)
            if match:
                item = match.group(1).strip()
                amount = float(match.group(2))
                items.append((item, amount))
                total += amount
    return items, total, date[0] if date else "Unknown"

# Set page config
st.set_page_config(page_title="SmartBill Scanner", page_icon="📷", layout="centered")

# Add a custom header image (optional, you can replace the URL)
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

# OAuth configuration for GitHub
oauth_config = {
    "credentials": {
        "oauth": {
            "github": {
                "client_id": st.secrets["github_client_id"],
                "client_secret": st.secrets["github_client_secret"],
            }
        }
    },
    "cookie": {
        "expiry_days": 1,
        "key": "a-very-random-signature-key-1234567890",  # Change this to a random string for security!
        "name": "aibillscanner_cookie"
    },
    "preauthorized": {
        "emails": []
    }
}

authenticator = stauth.Authenticate(
    None,  # No user/passwords, using OAuth
    oauth_config['cookie']['name'],
    oauth_config['cookie']['key'],
    oauth_config['cookie']['expiry_days'],
    oauth_config['credentials'],
    oauth_config['preauthorized']
)

name, authentication_status, username = authenticator.login("Login", "main")

if authentication_status:
    st.sidebar.success(f"Welcome, {name or username}!")
    st.sidebar.title("SmartBill Scanner")
    st.sidebar.info("Upload your bill and get instant results!")

    st.title("SmartBill Scanner")
    st.header("Upload Your Bill")

    api_key = st.secrets["ocr_space_api_key"] if "ocr_space_api_key" in st.secrets else "K86392130988957"

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