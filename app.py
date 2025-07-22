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

# Main logic
if pdf_file and search_button:
    with st.spinner("🔍 Extracting from PDF..."):
        doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
        
        # Extract all lines
        lines = []
        for page in doc:
            page_lines = page.get_text("text").splitlines()
            lines += [line.strip() for line in page_lines if line.strip()]
        
        # First 5 lines are headers
        headers = lines[:5]
        data_lines = lines[5:]
        num_fields = len(headers)

        # Group every N lines as one row
        records = [data_lines[i:i+num_fields] for i in range(0, len(data_lines), num_fields)
                   if len(data_lines[i:i+num_fields]) == num_fields]
        
        df = pd.DataFrame(records, columns=headers)
        st.success(f"✅ Extracted {len(df)} rows.")

        st.subheader("📋 Full Table")
        st.dataframe(df, use_container_width=True)

        # Pasted search values
        pasted_values = [x.strip() for x in input_text.splitlines() if x.strip()]
        matched_df = df[df.apply(lambda row: any(val in str(cell) for val in pasted_values for cell in row), axis=1)]

        st.subheader("🎯 Matched Results")
        st.success(f"✅ Found {len(matched_df)} matching row(s).")
        st.dataframe(matched_df, use_container_width=True)

        # Download button
        output = io.BytesIO()
        matched_df.to_excel(output, index=False)
        st.download_button("📥 Download Matched Results as Excel",
                           data=output.getvalue(),
                           file_name="matched_results.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
