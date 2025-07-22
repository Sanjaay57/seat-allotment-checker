import streamlit as st
import fitz  # PyMuPDF
import pandas as pd
import io

st.set_page_config(page_title="🎓 Merit List Checker", layout="centered")
st.title("🎓 Merit List Checker (Structured Search Tool)")

# Upload Section
uploaded_pdf = st.file_uploader("📄 Upload Merit List PDF", type=["pdf"])
pasted_ids = st.text_area("🔍 Paste Roll or Application Numbers (one per line):", height=150)
search_button = st.button("🔎 Search")

# === Helper to detect header row ===
def detect_headers(lines):
    for idx, line in enumerate(lines):
        if any(keyword in line.upper() for keyword in ["MERIT", "REGISTRATION", "ROLL", "CATEGORY", "MARKS"]):
            headers = [h.strip() for h in line.split("  ") if h.strip()]
            return idx, headers
    return None, []

# === Extract and Structure PDF ===
if uploaded_pdf and search_button:
    with st.spinner("🔍 Extracting and analyzing..."):
        # Read full text from PDF
        doc = fitz.open(stream=uploaded_pdf.read(), filetype="pdf")
        all_lines = []
        for page in doc:
            blocks = page.get_text("dict")["blocks"]
            for block in blocks:
                if "lines" not in block:
                    continue
                for line in block["lines"]:
                    row_text = " ".join([span["text"] for span in line["spans"]]).strip()
                    if row_text:
                        all_lines.append(row_text)

        # Detect headers
        header_index, headers = detect_headers(all_lines)
        if not headers:
            st.error("❌ Failed to detect headers in the PDF.")
        else:
            # Parse rows
            data_lines = all_lines[header_index + 1:]
            structured = []
            for line in data_lines:
                row = [cell.strip() for cell in line.split("  ") if cell.strip()]
                if len(row) >= len(headers):
                    structured.append(row[:len(headers)])

            df = pd.DataFrame(structured, columns=headers)

            # Match pasted input
            search_values = set(x.strip() for x in pasted_ids.splitlines() if x.strip())
            match_cols = [col for col in df.columns if any(key in col.lower() for key in ["roll", "reg", "application"])]
            
            if not match_cols:
                st.warning("⚠️ No matching column like 'Roll No' or 'Application No' found in headers.")
                st.dataframe(df)
            else:
                # Search all matching columns
                matched_df = df[df[match_cols[0]].astype(str).isin(search_values)]
                st.success(f"✅ Found {len(matched_df)} matching entries.")
                st.dataframe(matched_df, use_container_width=True)

                # Excel Download
                output = io.BytesIO()
                matched_df.to_excel(output, index=False)
                st.download_button("📥 Download Matched Entries (Excel)", data=output.getvalue(),
                                   file_name="Matched_Results.xlsx",
                                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
