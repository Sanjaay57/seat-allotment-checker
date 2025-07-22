import streamlit as st
from pdf2image import convert_from_bytes
import pytesseract
from io import BytesIO
import tempfile

# Set up Tesseract path (Windows only)
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

st.set_page_config(page_title="PDF OCR Extractor", layout="centered")

st.title("📄 OCR PDF Text Extractor")
st.markdown("Upload a scanned PDF. This app will convert it to text using OCR (Tesseract).")

uploaded_file = st.file_uploader("📎 Upload Scanned PDF", type=["pdf"])

if uploaded_file:
    with st.spinner("🔄 Converting PDF to text..."):
        try:
            # Convert PDF pages to images
            images = convert_from_bytes(uploaded_file.read(), dpi=300)

            all_text = ""
            for i, img in enumerate(images):
                text = pytesseract.image_to_string(img)
                all_text += f"\n\n--- Page {i+1} ---\n{text}"

            st.success("✅ OCR completed!")
            st.text_area("📄 Extracted Text", all_text, height=300)

            # Allow user to download the result
            result_bytes = BytesIO(all_text.encode("utf-8"))
            st.download_button("📥 Download as .txt", data=result_bytes, file_name="ocr_output.txt")

        except Exception as e:
            st.error(f"❌ An error occurred: {e}")
