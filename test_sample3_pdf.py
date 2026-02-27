import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
from src.engine import extract_text_from_docx, get_document_metadata
from src.formatter import generate_pdf

def test_sample3():
    text = extract_text_from_docx("assets/Sample 3.docx")
    meta = get_document_metadata(text)
    try:
        pdf_bytes = generate_pdf(meta, text)
        print("SUCCESS! PDF Generated successfully. Length:", len(pdf_bytes))
    except Exception as e:
        print("FAILED:", e)
        sys.exit(1)

test_sample3()
