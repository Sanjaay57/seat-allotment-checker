import streamlit as st
import fitz  # PyMuPDF
import pandas as pd
import re
import io

st.set_page_config(page_title="🎓 Horizontal PDF Merit Checker", layout="centered")
st.title("🎓 Horizontal Table Merit PDF Checker")

# Upload and input
pdf_file = st.file_uploader("📄 Upload Merit List PDF", type=["pdf"])
input_text = st.text_area("🔍 Paste Roll / Application / Reg. Numbers (one per line):", height=150)
search_button = st.button("🔎 Extract & Search")

# Heuristic: check if line looks like header
def looks_like_header(line):
    keywords = ["merit", "applicant", "registration", "roll", "category", "marks", "obtained"]
    return sum(1 for k in keywords if k in line.lower()) >= 3

if pdf_file and search_button:
    with st.spinner("🔍 Processing PDF..."):
        doc = fitz.open(stream=pdf_file.read(), filetype="pdf")

        # Step 1: Read all lines
        lines = []
        for page in doc:
            lines += [line.strip() for line in page.get_text("text").splitlines() if line.strip()]

        # Step 2: Identify first header line
        header_line = None
        header_fields = []
        data_rows = []

        for i, line in enumerate(lines):
            if looks_like_header(line):
                header_line = line
                header_fields = re.split(r"\s{2,}", header_line)
                break

        if not header_fields:
            st.error("⚠️ Could not detect header row. Try with a cleaner PDF.")
        else:
            # Step 3: Parse remaining lines into rows
            for line in lines[i+1:]:
                if looks_like_header(line) or re.search(r"Page\s+\d+\s+of\s+\d+", line, re.IGNORECASE):
                    continue  # skip repeated headers and page numbers
                row = re.split(r"\s{2,}", line)
                if len(row) == len(header_fields):  # only accept full rows
                    data_rows.append(row)

            df = pd.DataFrame(data_rows, columns=header_fields)
            st.success(f"✅ Extracted {len(df)} rows from horizontal table.")

            st.subheader("📋 Full Table")
            st.dataframe(df, use_container_width=True, hide_index=True)

            # Step 4: Match pasted values
            pasted_values = [x.strip() for x in input_text.splitlines() if x.strip()]
            matched_df = df[df.apply(lambda row: any(val in str(cell) for val in pasted_values for cell in row), axis=1)]

            st.subheader("🎯 Matched Results")
            if not matched_df.empty:
                st.success(f"✅ Found {len(matched_df)} matching row(s).")
                st.dataframe(matched_df, use_container_width=True, hide_index=True)

                # Step 5: Download
                output = io.BytesIO()
                matched_df.to_excel(output, index=False)
                st.download_button("📥 Download Matched Results as Excel",
                                   data=output.getvalue(),
                                   file_name="matched_results.xlsx",
                                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            else:
                st.warning("⚠️ No matches found. Please check your pasted data.")
