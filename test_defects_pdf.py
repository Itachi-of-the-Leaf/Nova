import sys
import os

# Add backend dir to python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from src.engine import extract_text_from_docx, get_document_metadata
from src.formatter import generate_pdf

def test_sample3_compiles():
    file_path = "assets/Sample 3.docx"
    print(f"Extracting text from {file_path}...")
    raw_text = extract_text_from_docx(file_path)
    
    print("Getting metadata...")
    metadata = get_document_metadata(raw_text)
    
    print("Generating PDF...")
    try:
        pdf_bytes = generate_pdf(metadata, raw_text)
        print("SUCCESS! PDF Generated successfully.")
        assert pdf_bytes.startswith(b'%PDF'), "Output is not a valid PDF"
    except Exception as e:
        print(f"FAILURE: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_sample3_compiles()
