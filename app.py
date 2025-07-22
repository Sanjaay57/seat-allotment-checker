import streamlit as st
import fitz  # PyMuPDF
import pandas as pd
import io

st.set_page_config(page_title="Dynamic Merit PDF Parser", layout="centered")
st.title("🎓 Merit List Extractor & Search Tool")

# Upload and input
pdf_file = st.file_uploader("📄 Upload Merit List PDF", type=["pdf"])
input_text = st.text_area("🔍 Paste Roll / Application / Reg. Numbers (one per line):", height=150)
search_button = st.button("🔎 Extract & Search")

# Helper: Detect headers (5-7 consecutive non-numeric, uppercase/title lines)
def detect_header_lines(lines, max_header_len=7):
    for i in range(len(lines) - max_header_len):
        candidate = lines[i:i + max_header_len]
        if all((x.isupper() or x.istitle()) and not any(char.isdigit() for char in x) for x in candidate):
            return i, candidate
    return None, []

if pdf_file and search_button:
    with st.spinner("⏳ Processing PDF..."):
        doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
        all_lines = []

        # Extract all text lines
        for page in doc:
            blocks = page.get_text("dict")["blocks"]
            for block in blocks:
                if "lines" not in block:
                    continue
                for line in block["lines"]:
                    text = " ".join(span["text"] for span in line["spans"]).strip()
                    if text:
                        all_lines.append(text)

        # Detect headers
        start_idx, headers = detect_header_lines(all_lines)
        if not headers:
            st.error("❌ Could not automatically detect headers in the PDF.")
        else:
            data_lines = all_lines[start_idx + len(headers):]
            num_fields = len(headers)

            # Group every N lines into a row
            records = [data_lines[i:i + num_fields] for i in range(0, len(data_lines), num_fields)
                       if len(data_lines[i:i + num_fields]) == num_fields]
            df = pd.DataFrame(records, columns=headers)
            st.success(f"✅ Detected {len(df)} records with {num_fields} fields.")

            # Show full table
            st.subheader("📋 Full Extracted Table")
            st.dataframe(df, use_container_width=True)

            # Search pasted IDs
            if input_text:
                search_terms = [x.strip() for x in input_text.splitlines() if x.strip()]
                matched_df = df[df.apply(lambda row: any(term in str(cell) for term in search_terms for cell in row), axis=1)]

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
