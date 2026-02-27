import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
from src.engine import extract_text_from_docx, get_document_metadata
import json

def test_samplex():
    text = extract_text_from_docx("assets/Sample X.docx")
    print("--- RAW TEXT ---")
    print(text[:1000])  # Print top 1000 chars to see what unstructured gave us
    print("----------------")
    meta = get_document_metadata(text)
    print("--- METADATA ---")
    print(json.dumps(meta, indent=2))
    
    # Check if we should fail (so we can see the exact output)
    # The fix hasn't been applied yet, so we just want to look at it.

test_samplex()
