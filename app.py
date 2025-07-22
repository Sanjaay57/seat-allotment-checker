import streamlit as st
import fitz  # PyMuPDF
import pandas as pd
import io
import re

# --- Streamlit Page Configuration ---
st.set_page_config(page_title="🎓 Merit PDF Checker", layout="wide")
st.title("🎓 Merit List PDF Extractor & Search Tool")
st.write("Upload a merit list in PDF format and paste Roll Numbers or Registration Numbers to find specific records.")

# --- File Upload and User Input ---
# Use columns for a cleaner layout
col1, col2 = st.columns([1, 1])

with col1:
    pdf_file = st.file_uploader("📄 **Upload Merit List PDF**", type=["pdf"])

with col2:
    input_text = st.text_area(
        "📝 **Paste Roll / Registration Numbers** (one per line):",
        height=150,
        placeholder="801437\n25REG00000924\n..."
    )

search_button = st.button("🔎 **Extract & Search Results**", use_container_width=True)

# --- Main Logic ---
if search_button and pdf_file and input_text:
    with st.spinner("Analyzing PDF and searching for records..."):
        try:
            # --- 1. PDF Text Extraction ---
            doc = fitz.open(stream=pdf_file.read(), filetype="pdf")

            # --- 2. Define Headers and Data Storage ---
            # Using static headers is more reliable than dynamic parsing from raw text.
            # These headers correspond to the capturing groups in our regex.
            headers = ["Merit Rank", "Applicant Registration No.", "Entrance Roll Number", "Category", "Marks Obtained in NFAT"]
            all_rows = []

            # --- 3. Define the Regular Expression for a Data Row ---
            # This regex is designed to be robust and capture the five key fields,
            # even when the "Category" field contains spaces.
            # It looks for:
            # 1. (\d+)                      - Merit Rank (one or more digits)
            # 2. ([A-Z0-9\S]+)              - Registration Number (a block of non-space chars)
            # 3. (\d{6,})                   - Entrance Roll Number (6 or more digits)
            # 4. (.+?)                      - Category (any characters, non-greedy)
            # 5. ([\d\.:]+)$                - Marks (digits, dots, or colons at the end of the line)
            data_row_regex = re.compile(r"^(\d+)\s+([A-Z0-9\S]+)\s+(\d{6,})\s+(.+?)\s+([\d\.:]+)$")

            # --- 4. Process Each Page ---
            for page_num, page in enumerate(doc):
                text = page.get_text("text")
                lines = text.splitlines()

                for line in lines:
                    # Check if the line matches our data row pattern
                    match = data_row_regex.match(line.strip())
                    if match:
                        # Extract all 5 captured groups from the match
                        row_data = list(match.groups())
                        
                        # Clean the marks column (replace ':' with '.' for consistency)
                        row_data[4] = row_data[4].replace(':', '.')
                        
                        all_rows.append(row_data)

            # --- 5. Create and Display DataFrame ---
            if not all_rows:
                st.error("❌ **No data found.** Could not find any data matching the expected table format in the PDF.")
            else:
                df = pd.DataFrame(all_rows, columns=headers)
                
                # Convert marks to a numeric type for correct sorting
                df["Marks Obtained in NFAT"] = pd.to_numeric(df["Marks Obtained in NFAT"], errors='coerce')

                st.success(f"✅ **Extraction Complete:** Found and processed **{len(df)}** records from the PDF.")

                # --- 6. Search for Matched Records ---
                pasted_values = [v.strip() for v in input_text.splitlines() if v.strip()]

                # Search in both registration number and roll number columns
                matched_df = df[
                    df["Applicant Registration No."].str.strip().isin(pasted_values) |
                    df["Entrance Roll Number"].str.strip().isin(pasted_values)
                ]

                st.subheader("🎯 Matched Results")
                if not matched_df.empty:
                    st.dataframe(matched_df, use_container_width=True, hide_index=True)

                    # --- 7. Provide Download Button for Matched Results ---
                    output = io.BytesIO()
                    matched_df.to_excel(output, index=False, sheet_name="Matched_Results")
                    st.download_button(
                        label="📥 **Download Matched Results as Excel**",
                        data=output.getvalue(),
                        file_name="matched_merit_list_results.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                else:
                    st.warning("⚠️ No matching records were found for the numbers you provided.")

                # --- Optional: Display Full Extracted Table ---
                with st.expander("📂 **View Full Extracted Merit List**"):
                    st.dataframe(df, use_container_width=True, hide_index=True)

        except Exception as e:
            st.error(f"An error occurred: {e}")

# Instructions for when the app first loads or buttons aren't pressed
elif search_button:
    st.warning("Please upload a PDF and paste at least one number to search.")
