
import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import tempfile
import re

st.set_page_config(page_title="Counselling/Allotment Checker", layout="wide")
st.title("🎓 Seat Allotment / Counselling Checker")

# Step 1: Paste Input
pasted_data = st.text_area("📋 Paste Roll Numbers or Application Numbers (one per line):", height=200)
pasted_list = [x.strip() for x in pasted_data.splitlines() if x.strip()]

# Step 2: Upload PDF
uploaded_file = st.file_uploader("📄 Upload Seat Allotment PDF", type=["pdf"])

# Helper: OCR page image
def ocr_pdf_page(pdf_bytes, page_num):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page = doc.load_page(page_num)
    pix = page.get_pixmap(dpi=300)
    img = Image.open(io.BytesIO(pix.tobytes("png")))
    text = pytesseract.image_to_string(img)
    return text

# Helper: extract table from text
def extract_table_rows(text):
    lines = text.splitlines()
    headers = []
    data_rows = []
    for line in lines:
        clean_line = line.strip()
        if not clean_line:
            continue
        # Heuristic: find header
        if any(keyword in clean_line.lower() for keyword in ["roll", "application", "category", "institute", "remarks", "seat"]):
            headers = re.split(r"\s{2,}", clean_line)
        elif headers:
            row = re.split(r"\s{2,}", clean_line)
            if len(row) >= len(headers):
                data_rows.append(row[:len(headers)])
    return headers, data_rows

# Process PDF
if st.button("🔍 Search") and uploaded_file and pasted_list:
    with st.spinner("Processing PDF..."):
        pdf_bytes = uploaded_file.read()
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        all_rows = []
        final_headers = []

        for page_num in range(len(doc)):
            text = doc[page_num].get_text("text")

            if not text.strip():  # fallback to OCR
                text = ocr_pdf_page(pdf_bytes, page_num)

            headers, rows = extract_table_rows(text)
            if headers and rows:
                final_headers = headers
                all_rows.extend(rows)

        if not final_headers or not all_rows:
            st.error("⚠️ Could not detect table or headers. Please try with a clearer PDF.")
        else:
            df = pd.DataFrame(all_rows, columns=final_headers)

            # Match with pasted list
            match_col = None
            for col in df.columns:
                if any(x in col.lower() for x in ["roll", "application"]):
                    match_col = col
                    break

            if not match_col:
                st.warning("⚠️ Could not find a matching column like 'Roll No' or 'Application No'.")
            else:
                df[match_col] = df[match_col].astype(str).str.strip()
                pasted_list_clean = [x.strip() for x in pasted_list]
                matched_df = df[df[match_col].isin(pasted_list_clean)]

                st.success(f"✅ Found {len(matched_df)} match(es).")
                st.dataframe(matched_df, use_container_width=True)

                # Download button
                def convert_df(df):
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        df.to_excel(writer, index=False, sheet_name='Matched')
                    return output.getvalue()

                st.download_button(
                    label="📥 Download Matched Results as Excel",
                    data=convert_df(matched_df),
                    file_name="matched_results.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
