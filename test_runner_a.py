import sys
sys.path.append("backend")

import logging
logging.basicConfig(level=logging.DEBUG)

from src.engine import extract_text_from_docx

print("\n--- Testing Sample X ---")
text = extract_text_from_docx("assets/Sample_X_Input.docx")
print("Extraction complete.")
