import streamlit as st
import fitz  # PyMuPDF
import pandas as pd
import io
import re

st.set_page_config(page_title="🎓 Merit PDF Checker", layout="centered")
st.title("🎓 Merit List PDF Checker (Robust Extraction)")

# Upload and input
pdf_file = st.file_uploader("📄 Upload Merit List PDF", type=["pdf"])
input_text = st.text_area("🔍 Paste Roll / Application / Reg. Numbers (one per line):", height=150)
search_button = st.button("🔎 Extract & Search")

# Main logic
if pdf_file and search_button:
    with st.spinner("🔍 Extracting from PDF..."):
        doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
        
        all_extracted_records = []
        headers = []

        for page_num, page in enumerate(doc):
            text = page.get_text("text")
            lines = [line.strip() for line in text.splitlines() if line.strip()]

            # Attempt to find headers dynamically on the first page or if not found yet
            if not headers:
                # Common header patterns to look for
                potential_headers = [
                    "MERIT", "APPLICANT REGISTRATION NO.", "ENTRANCE ROLL NUMBER", 
                    "CATEGORY", "MARKS OBTAINED IN NFAT", "MARKS C" # "MARKS C" from image_1e5900.png
                ]
                # Look for a line that contains several of these keywords
                for line_idx, line in enumerate(lines):
                    if all(header_part in line for header_part in ["MERIT", "APPLICANT REGISTRATION"]):
                        # This line likely contains the headers
                        headers = [h.strip() for h in re.split(r'\s{2,}|(?<=\D)(?=\d)|(?<=\d)(?=\D)', line) if h.strip()]
                        # Clean up headers, e.g., combine "APPLICANT REGISTRATION NO."
                        if "APPLICANT REGISTRATION" in headers and "NO." in headers:
                            idx1 = headers.index("APPLICANT REGISTRATION")
                            idx2 = headers.index("NO.")
                            if idx2 == idx1 + 1:
                                headers[idx1] = "APPLICANT REGISTRATION NO."
                                headers.pop(idx2)
                        
                        if "ENTRANCE" in headers and "ROLL NUMBER" in headers:
                             idx1 = headers.index("ENTRANCE")
                             idx2 = headers.index("ROLL NUMBER")
                             if idx2 == idx1 + 1:
                                 headers[idx1] = "ENTRANCE ROLL NUMBER"
                                 headers.pop(idx2)
                        
                        # Handle "MARKS C" as a header if present
                        if "MARKS C" in headers:
                            headers[headers.index("MARKS C")] = "MARKS OBTAINED IN NFAT" # Harmonize if possible


                        # Start processing data from after the header line
                        lines = lines[line_idx + 1:]
                        break
            
            # If headers are found, process the remaining lines as potential data
            if headers:
                num_fields = len(headers)
                current_record = []
                for line in lines:
                    # Heuristic to determine if a line is part of a data record
                    # Check for common patterns: a number at the start, "25REG" pattern, "800" for roll numbers
                    if re.match(r'^\d+(\.\d+)?$', line) or re.match(r'^\d{2}REG\d{7,}', line) or re.match(r'^\d{6,}', line):
                        current_record.append(line)
                        if len(current_record) == num_fields:
                            all_extracted_records.append(current_record)
                            current_record = []
                    else:
                        # If the line doesn't match a data pattern, it might be a continuation of the last field
                        # Or it might be page number/irrelevant text.
                        # For now, we'll try to append it to the last field if a record is partially built
                        # This is a very basic attempt and might need more sophistication based on actual PDF structure
                        if current_record and not re.match(r'Page \d+ of \d+', line): # Avoid page numbers
                            # Try to append if it looks like a continuation of a multi-word field,
                            # e.g., "NATIONAL SCHOOL OF MANAGEMENT STUDIES" being split
                            # For now, we'll assume each field is on its own line for this structure.
                            # If a field spans multiple lines, this part needs more robust logic.
                            pass # We are assuming one field per line for these records

        if headers and all_extracted_records:
            df = pd.DataFrame(all_extracted_records, columns=headers)
            st.success(f"✅ Extracted {len(df)} rows.")

            st.subheader("📋 Full Table")
            st.dataframe(df, use_container_width=True, hide_index=True)

            # Pasted search values
            pasted_values = [x.strip() for x in input_text.splitlines() if x.strip()]
            
            # Search across all columns for the pasted values
            matched_df = df[df.apply(lambda row: any(str(val).strip() == pasted_value for pasted_value in pasted_values for val in row), axis=1)]

            st.subheader("🎯 Matched Results")
            if not matched_df.empty:
                st.success(f"✅ Found {len(matched_df)} matching row(s).")
                st.dataframe(matched_df, use_container_width=True, hide_index=True)

                # Download button
                output = io.BytesIO()
                matched_df.to_excel(output, index=False)
                st.download_button("📥 Download Matched Results as Excel",
                                   data=output.getvalue(),
                                   file_name="matched_results.xlsx",
                                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            else:
                st.warning("No matching records found for the provided input.")
        else:
            st.error("❌ Could not extract data or headers. Please ensure the PDF contains a clear tabular structure.")
