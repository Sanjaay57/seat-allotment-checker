import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
import io

st.set_page_config(page_title="Seat Allotment Checker", layout="centered")
st.title("🎓 Seat Allotment Checker")

# --- Input Section ---
uploaded_pdf = st.file_uploader("📄 Upload PDF", type=["pdf"])
search_input = st.text_area("🔍 Enter values to search (one per line):", height=150, placeholder="Paste Application Nos, Roll Nos, etc.")
search_button = st.button("🔎 Search")

if uploaded_pdf and search_input and search_button:
    with st.spinner("Processing PDF..."):
        doc = fitz.open(stream=uploaded_pdf.read(), filetype="pdf")
        search_terms = set(x.strip() for x in search_input.strip().splitlines() if x.strip())

        matches = []
        for page in doc:
            text = page.get_text()
            lines = text.splitlines()

            for line in lines:
                if any(term in line for term in search_terms):
                    matches.append(line.strip())

        if matches:
            # Attempt to split by multiple spaces or tabs
            structured_data = []
            for line in matches:
                columns = [col.strip() for col in line.split("  ") if col.strip()]
                structured_data.append(columns)

            # Determine max columns
            max_cols = max(len(row) for row in structured_data)
            col_names = [f"Field {i+1}" for i in range(max_cols)]

            # Pad rows to have equal length
            padded_data = [row + [""] * (max_cols - len(row)) for row in structured_data]
            df = pd.DataFrame(padded_data, columns=col_names)

            st.success(f"✅ Found {len(matches)} matching entries.")
            st.dataframe(df, use_container_width=True)

            # Excel Download
            excel_data = io.BytesIO()
            df.to_excel(excel_data, index=False)
            st.download_button("📥 Download as Excel", data=excel_data.getvalue(), file_name="Matched_Results.xlsx")
        else:
            st.warning("🔍 No matches found in the PDF.")
