import streamlit as st
import fitz  # PyMuPDF
import pandas as pd
import io

st.set_page_config(page_title="Seat Allotment / Counselling Checker", layout="centered")

st.markdown("<h1 style='text-align: center;'>🎓 Seat Allotment / Counselling Checker</h1>", unsafe_allow_html=True)

# Input box - Centered
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    user_input = st.text_area("📋 Paste Roll/Application Numbers (one per line):", height=200)

# PDF upload - Centered
with col2:
    uploaded_pdf = st.file_uploader("📤 Upload Seat Allotment PDF", type="pdf")

# Clean input values
search_terms = set(line.strip() for line in user_input.splitlines() if line.strip())

# Search button
with col2:
    if st.button("🔍 Search") and uploaded_pdf and search_terms:
        matches = []
        pdf_doc = fitz.open(stream=uploaded_pdf.read(), filetype="pdf")

        for page in pdf_doc:
            lines = page.get_text().split('\n')
            for line in lines:
                for term in search_terms:
                    if term in line:
                        matches.append(line.strip())
                        break  # Avoid duplicate if multiple terms in same line

        if matches:
            # Try to split lines into structured table using multiple spaces
            def split_line(line):
                return [part.strip() for part in line.split("  ") if part.strip()]

            split_matches = [split_line(line) for line in matches]
            max_cols = max(len(row) for row in split_matches)

            # Normalize all rows to same length
            normalized_data = [row + [""] * (max_cols - len(row)) for row in split_matches]

            df = pd.DataFrame(normalized_data)
            df.columns = [f"Field {i+1}" for i in range(df.shape[1])]

            st.success(f"✅ Found {len(matches)} matching entries.")
            st.dataframe(df, use_container_width=True)

            # Download option
            excel_data = io.BytesIO()
            df.to_excel(excel_data, index=False)
            st.download_button("📥 Download as Excel", data=excel_data.getvalue(), file_name="Matched_Results.xlsx")
        else:
            st.warning("⚠️ No matches found. Please check your pasted data and try again.")
    elif st.button("🔍 Search"):
        st.error("❌ Please upload a PDF and enter roll/application numbers.")
