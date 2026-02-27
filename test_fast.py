import sys
sys.path.append("backend")
from src.engine import extract_text_from_docx, get_document_metadata
import logging
logging.basicConfig(level=logging.ERROR)

print("--- Fast Extraction Test ---")
t3 = extract_text_from_docx("assets/Sample_3_Input.docx")
m3 = get_document_metadata(t3)
print("TEST 3 TITLE:", m3["title"])

tx = extract_text_from_docx("assets/Sample_X_Input.docx")
mx = get_document_metadata(tx)
print("TEST X TITLE:", mx["title"])
