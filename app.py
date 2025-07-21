import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import re

st.set_page_config(page_title="Counselling/Allotment Checker", layout="wide")
st.title("🎓 Seat Allotment / Counselling Checker")

# Step 1: Paste Input
pasted_data = st.text_area("📋 Paste Roll/Application Numbers (one per line):", height=200)
pasted_list = [x.strip() for x in pasted_data.splitlines() if x.strip()]

# Step 2: Upload PDF
uploaded_file = st.file_uploader("📄 Upload Seat Allotment PDF", type=["pdf"])

# OCR fallback
def ocr_pdf_page(pdf_bytes, page_num):
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        page = doc.load_page(page_num)
        pix = page.get_pixmap(dpi=300)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        text = pytesseract.image_to_string(img)
        return text
    except Exception:
        return ""

# Extract header and rows
def extract_table_from_text(text):
    lines = text.splitlines()
    headers = []
    data_rows = []
    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Header detection
        if not headers and any(keyword in line.lower() for keyword in ["roll", "application", "seat", "category", "rank", "remarks"]):
            headers = re.split(r"\s{2,}", line.strip())
            continue

        if headers:
            row = re.split(r"\s{2,}", line.strip())
            if len(row) >= len(headers):  # Match or exceed header length
                data_rows.append(row[:len(headers)])

    return headers, data_rows

# Streamlit logic
if st.button("🔍 Search") and uploaded_file and pasted_list:
    with st.spinner("Analyzing PDF..."):
        pdf_bytes = uploaded_file.read()
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        full_rows = []
        detected_headers = []

        for page_num in range(len(doc)):
            text = doc[page_num].get_text("text")
            if not text.strip():  # Fallback to OCR
                text = ocr_pdf_page(pdf_bytes, page_num)

            headers, rows = extract_table_from_text(text)
            if headers and rows:
                if not detected_headers:
                    detected_headers = headers
                full_rows.extend(rows)

        if not detected_headers or not full_rows:
            st.error("❌ No valid table or headers detected. Please try another PDF.")
        else:
            df = pd.DataFrame(full_rows, columns=detected_headers)

            # Detect the matching column
            match_col = None
            for col in df.columns:
                if any(key in col.lower() for key in ["roll", "application", "reg", "id"]):
                    match_col = col
                    break

            if not match_col:
                st.warning("⚠️ Could not find a 'Roll No' or 'Application No' column.")
            else:
                df[match_col] = df[match_col].astype(str).str.strip()
                matches = df[df[match_col].isin(pasted_list)]

                if matches.empty:
                    st.info("🔍 No matches found.")
                else:
                    st.success(f"✅ Found {len(matches)} match(es).")
                    st.dataframe(matches, use_container_width=True)

                    # Download Excel
                    def convert_df(df):
                        output = io.BytesIO()
                        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                            df.to_excel(writer, index=False, sheet_name="Matched")
                        return output.getvalue()

                    st.download_button(
                        "📥 Download Matched Results as Excel",
                        data=convert_df(matches),
                        file_name="matched_results.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
