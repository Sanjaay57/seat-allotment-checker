import streamlit as st
import fitz  # PyMuPDF
import pandas as pd
import io

st.set_page_config(page_title="Merit List Extractor", layout="centered")
st.title("🎓 Merit List Extractor & Search Tool")

# File Upload
uploaded_pdf = st.file_uploader("📄 Upload a Merit List PDF (vertical format)", type=["pdf"])

if uploaded_pdf:
    with st.spinner("🔄 Extracting data from PDF..."):
        # Open and extract lines from PDF
        doc = fitz.open(stream=uploaded_pdf.read(), filetype="pdf")
        all_lines = []
        for page in doc:
            blocks = page.get_text("dict")["blocks"]
            for block in blocks:
                if "lines" not in block:
                    continue
                for line in block["lines"]:
                    row = " ".join([span["text"] for span in line["spans"]]).strip()
                    if row:
                        all_lines.append(row)

        # Extract headers and data
        headers = all_lines[:5]  # Assumes 5 headers
        data_lines = all_lines[5:]
        rows = [data_lines[i:i+5] for i in range(0, len(data_lines), 5) if len(data_lines[i:i+5]) == 5]

        if rows:
            df = pd.DataFrame(rows, columns=headers)
            st.success(f"✅ Extracted {len(df)} rows from the merit list.")

            # Optional Search
            search_term = st.text_input("🔍 Search by Registration Number or Roll Number")
            if search_term:
                df_filtered = df[df.apply(lambda row: row.astype(str).str.contains(search_term, case=False).any(), axis=1)]
                st.write(f"🔎 Showing results for: **{search_term}**")
                st.dataframe(df_filtered, use_container_width=True)
            else:
                st.dataframe(df, use_container_width=True)

            # Download
            output = io.BytesIO()
            df.to_excel(output, index=False)
            st.download_button("📥 Download Full Merit List (Excel)", data=output.getvalue(),
                               file_name="merit_list.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        else:
            st.warning("⚠️ Could not detect structured data from this PDF format.")
