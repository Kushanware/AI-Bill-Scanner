import streamlit as st
import uuid
from ocr_utils import extract_text_from_image
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

# Simple session-based user_id (for demo; use real login for production)
if "user_id" not in st.session_state:
    st.session_state["user_id"] = str(uuid.uuid4())
current_user_id = st.session_state["user_id"]

st.markdown("---")
st.header("Upload Your Bill")

uploaded_file = st.file_uploader("Upload your bill/receipt image", type=["jpg", "png", "jpeg"])

if uploaded_file:
    text = extract_text_from_image(uploaded_file)
    items, total, date = extract_fields(text)
    
    st.success("✅ Bill scanned successfully!")
    st.markdown("---")
    st.subheader("🧾 Extracted Items:")
    st.table(items)
    st.subheader("💰 Total Amount:")
    st.info(f"₹{total}")
    st.subheader("📅 Bill Date:")
    st.info(date)

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