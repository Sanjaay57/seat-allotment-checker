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
if search_button and pdf_file:
    with st.spinner("Analyzing PDF and searching for records..."):
        try:
            # --- 1. PDF Text Extraction ---
            doc = fitz.open(stream=pdf_file.read(), filetype="pdf")

            # --- 2. Define Headers and Data Storage ---
            headers = ["Merit Rank", "Applicant Registration No.", "Entrance Roll Number", "Category", "Marks Obtained in NFAT"]
            all_rows = []
            
            # **FIX**: Variable to hold the rank for rows where it's not explicitly listed
            last_merit_rank = None

            # --- 3. Define Regular Expressions for Data Rows ---
            # **FIX**: Two patterns are now used. One for rows with a rank, and one for rows without.
            
            # Pattern for a standard row starting with a merit rank
            regex_with_rank = re.compile(r"^(\d+)\s+([A-Z0-9\S]+)\s+(\d{6,})\s+(.+?)\s+([\d\.:]+)$")
            
            # Pattern for a row that is missing the initial merit rank
            regex_without_rank = re.compile(r"^([A-Z0-9\S]+)\s+(\d{6,})\s+(.+?)\s+([\d\.:]+)$")

            # --- 4. Process Each Page ---
            for page_num, page in enumerate(doc):
                text = page.get_text("text")
                lines = text.splitlines()

                for line in lines:
                    line = line.strip()
                    # First, try to match the pattern that includes the rank
                    match_with_rank = regex_with_rank.match(line)
                    
                    if match_with_rank:
                        row_data = list(match_with_rank.groups())
                        # This line has a rank, so we update our tracker
                        last_merit_rank = row_data[0]
                        # Clean the marks column for consistency
                        row_data[4] = row_data[4].replace(':', '.')
                        all_rows.append(row_data)
                    else:
                        # If the first pattern failed, try the one for rows without a rank
                        match_without_rank = regex_without_rank.match(line)
                        if match_without_rank and last_merit_rank:
                            # This row is missing a rank, so we use the last one we saw
                            row_data = list(match_without_rank.groups())
                            # **FIX**: Manually insert the last seen rank at the beginning of the list
                            row_data.insert(0, last_merit_rank)
                            # Clean the marks column
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

                # --- 6. Search for Matched Records if input is provided ---
                if input_text.strip():
                    pasted_values = [v.strip() for v in input_text.splitlines() if v.strip()]
                    
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

# Instructions for when the app first loads or button is pressed without a file
elif search_button:
    st.warning("Please upload a PDF file to begin.")
