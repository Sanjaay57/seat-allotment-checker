import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
import io

st.set_page_config(page_title="Seat Allotment Checker", layout="centered")
st.title("📋 Seat Allotment Search (Full Row Extract)")

uploaded_pdf = st.file_uploader("📄 Upload PDF", type=["pdf"])
search_input = st.text_area("🔍 Enter values to search (one per line):", height=150)
search_button = st.button("🔎 Search Now")

def extract_rows_with_layout(pdf_stream, terms):
    matches = []
    doc = fitz.open(stream=pdf_stream, filetype="pdf")

    for page in doc:
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            if "lines" not in block:
                continue
            for line in block["lines"]:
                row_text = " ".join([span["text"] for span in line["spans"]]).strip()
                if any(term in row_text for term in terms):
                    matches.append(row_text)
    return matches

if uploaded_pdf and search_input and search_button:
    with st.spinner("⏳ Processing PDF..."):
        search_terms = set(x.strip() for x in search_input.strip().splitlines() if x.strip())

        matches = extract_rows_with_layout(uploaded_pdf.read(), search_terms)

        if matches:
            # Try to split by consistent spacing
            structured = []
            for line in matches:
                parts = [p.strip() for p in line.split("  ") if p.strip()]
                structured.append(parts)

            # Normalize row lengths
            max_len = max(len(r) for r in structured)
            structured = [r + [""] * (max_len - len(r)) for r in structured]
            df = pd.DataFrame(structured, columns=[f"Field {i+1}" for i in range(max_len)])

            st.success(f"✅ Found {len(df)} matching entries.")
            st.dataframe(df, use_container_width=True)

            # Excel Download
            buffer = io.BytesIO()
            df.to_excel(buffer, index=False)
            st.download_button("📥 Download Results", data=buffer.getvalue(), file_name="Matches.xlsx")

        else:
            st.warning("🔍 No matches found in the PDF.")
