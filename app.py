import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import re

st.set_page_config(page_title="Seat Allotment Checker", layout="wide")
st.title("🎓 Seat Allotment / Counselling Checker")

# Centered layout using columns
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    pasted_data = st.text_area("📋 Paste Roll/Application Numbers (one per line):", height=200)
    pasted_list = [x.strip().upper() for x in pasted_data.splitlines() if x.strip()]
    uploaded_file = st.file_uploader("📄 Upload Seat Allotment PDF", type=["pdf"])

# OCR fallback for scanned pages
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

# Extract headers and rows from text
def extract_table_from_text(text):
    lines = text.splitlines()
    headers = []
    data_rows = []

    for line in lines:
        clean_line = line.strip()
        if not clean_line:
            continue

        if not headers and any(word in clean_line.lower() for word in ["roll", "application", "registration", "category", "merit", "marks"]):
            headers = re.split(r"\s{2,}", clean_line)
            continue

        if headers:
            row = re.split(r"\s{2,}", clean_line)
            if len(row) >= len(headers):
                data_rows.append(row[:len(headers)])

    return headers, data_rows

# Main logic
with col2:
    if st.button("🔍 Search") and uploaded_file and pasted_list:
        with st.spinner("🔄 Analyzing PDF..."):
            pdf_bytes = uploaded_file.read()
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")

            final_headers = []
            all_rows = []

            for page_num in range(len(doc)):
                text = doc[page_num].get_text("text")
                if not text.strip():
                    text = ocr_pdf_page(pdf_bytes, page_num)

                headers, rows = extract_table_from_text(text)
                if headers and rows:
                    if not final_headers:
                        final_headers = headers
                    all_rows.extend(rows)

            if not final_headers or not all_rows:
                st.error("❌ Could not detect a valid table with headers. Please try another PDF.")
            else:
                df = pd.DataFrame(all_rows, columns=final_headers)

                # Normalize column names
                df.columns = [col.strip().upper() for col in df.columns]

                # Normalize all cell values
                for col in df.columns:
                    df[col] = df[col].astype(str).str.strip().str.upper()

                pasted_set = set(pasted_list)

                # Detect matching columns
                match_cols = [col for col in df.columns if any(k in col for k in ["ROLL", "APPLICATION", "REGISTRATION", "ID"])]

                matched_df = pd.DataFrame()
                for col in match_cols:
                    matched = df[df[col].isin(pasted_set)]
                    matched_df = pd.concat([matched_df, matched], ignore_index=True)

                if matched_df.empty:
                    st.info("🔍 No matches found. Please check your pasted data and try again.")
                else:
                    st.success(f"✅ Found {len(matched_df)} match(es).")
                    st.dataframe(matched_df, use_container_width=True)

                    # Download matched data
                    def convert_df(df):
                        output = io.BytesIO()
                        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                            df.to_excel(writer, index=False, sheet_name="Matched")
                        return output.getvalue()

                    st.download_button(
                        label="📥 Download Matched Results as Excel",
                        data=convert_df(matched_df),
                        file_name="matched_results.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
