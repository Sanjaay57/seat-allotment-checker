import streamlit as st
import fitz  # PyMuPDF
import pandas as pd
import io
import re

st.set_page_config(page_title="🎓 Merit PDF Checker", layout="centered")
st.title("🎓 Merit List PDF Checker (Cleaned + Matched)")

# Upload and input
pdf_file = st.file_uploader("📄 Upload Merit List PDF", type=["pdf"])
input_text = st.text_area("🔍 Paste Roll / Application / Reg. Numbers (one per line):", height=150)
search_button = st.button("🔎 Extract & Search")

if pdf_file and search_button:
    with st.spinner("🔍 Extracting and Cleaning PDF..."):
        doc = fitz.open(stream=pdf_file.read(), filetype="pdf")

        # Step 1: Read all lines from all pages
        lines = []
        for page in doc:
            lines += [line.strip() for line in page.get_text("text").splitlines() if line.strip()]

        if len(lines) < 10:
            st.error("⚠️ Not enough content in the PDF.")
        else:
            # Step 2: Detect the first 5 lines as headers
            headers = lines[:5]
            num_fields = len(headers)

            # Step 3: Remove repeated headers and "Page X of Y" lines
            cleaned_lines = []
            for line in lines:
                if re.search(r"Page\s+\d+\s+of\s+\d+", line, re.IGNORECASE):
                    continue  # skip page numbers
                if line in headers:
                    continue  # skip repeated headers
                cleaned_lines.append(line)

            # Step 4: Group every num_fields lines into rows
            records = [cleaned_lines[i:i+num_fields] for i in range(0, len(cleaned_lines), num_fields)
                       if len(cleaned_lines[i:i+num_fields]) == num_fields]

            # Step 5: Convert to DataFrame
            df = pd.DataFrame(records, columns=headers)
            st.success(f"✅ Extracted {len(df)} clean records.")

            st.subheader("📋 Full Table")
            st.dataframe(df, use_container_width=True, hide_index=True)

            # Step 6: Search from pasted values
            pasted_values = [x.strip() for x in input_text.splitlines() if x.strip()]
            matched_df = df[df.apply(lambda row: any(val in str(cell) for val in pasted_values for cell in row), axis=1)]

            st.subheader("🎯 Matched Results")
            if not matched_df.empty:
                st.success(f"✅ Found {len(matched_df)} matching row(s).")
                st.dataframe(matched_df, use_container_width=True, hide_index=True)

                # Step 7: Download matched rows
                output = io.BytesIO()
                matched_df.to_excel(output, index=False)
                st.download_button("📥 Download Matched Results as Excel",
                                   data=output.getvalue(),
                                   file_name="matched_results.xlsx",
                                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            else:
                st.warning("⚠️ No matches found. Please check your pasted data.")
