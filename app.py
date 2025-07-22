import streamlit as st
import fitz  # PyMuPDF
import pandas as pd
import io

st.set_page_config(page_title="🎓 Merit PDF Checker", layout="centered")
st.title("🎓 Merit List PDF Checker (Structured Vertical Records)")

# Upload and input
pdf_file = st.file_uploader("📄 Upload Merit List PDF", type=["pdf"])
input_text = st.text_area("🔍 Paste Roll / Application / Reg. Numbers (one per line):", height=150)
search_button = st.button("🔎 Extract & Search")

if pdf_file and search_button:
    with st.spinner("🔍 Extracting from PDF..."):
        doc = fitz.open(stream=pdf_file.read(), filetype="pdf")

        # Read all lines
        lines = []
        for page in doc:
            page_lines = page.get_text("text").splitlines()
            lines += [line.strip() for line in page_lines if line.strip()]

        if len(lines) < 10:
            st.error("⚠️ Not enough content found in the PDF to process.")
        else:
            # Use first 5 lines as headers
            headers = lines[:5]
            num_fields = len(headers)

            # Remove repeated header blocks from lines
            cleaned_lines = []
            for i in range(0, len(lines), num_fields):
                block = lines[i:i+num_fields]
                if block == headers:
                    continue  # skip repeated header
                cleaned_lines.extend(block)

            # Group into rows
            records = [cleaned_lines[i:i+num_fields] for i in range(0, len(cleaned_lines), num_fields)
                       if len(cleaned_lines[i:i+num_fields]) == num_fields]

            df = pd.DataFrame(records, columns=headers)
            st.success(f"✅ Extracted {len(df)} rows after cleaning repeated headers.")

            st.subheader("📋 Full Table")
            st.dataframe(df, use_container_width=True, hide_index=True)

            # Search
            pasted_values = [x.strip() for x in input_text.splitlines() if x.strip()]
            matched_df = df[df.apply(lambda row: any(val in str(cell) for val in pasted_values for cell in row), axis=1)]

            st.subheader("🎯 Matched Results")
            if not matched_df.empty:
                st.success(f"✅ Found {len(matched_df)} matching row(s).")
                st.dataframe(matched_df, use_container_width=True, hide_index=True)

                output = io.BytesIO()
                matched_df.to_excel(output, index=False)
                st.download_button("📥 Download Matched Results as Excel",
                                   data=output.getvalue(),
                                   file_name="matched_results.xlsx",
                                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            else:
                st.warning("⚠️ No matches found. Please check your pasted data.")
