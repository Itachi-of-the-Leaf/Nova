import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
from src.engine import extract_text_from_docx, get_document_metadata
import json

def test_regression_samplex():
    text = extract_text_from_docx("assets/Sample X.docx")
    meta = get_document_metadata(text)
    
    print("--- EXTRACTED METADATA ---")
    print(json.dumps(meta, indent=2))
    
    title = meta.get("title", "")
    authors = meta.get("authors", "")
    confidence = meta.get("confidence", 0)
    
    expected_title = "A look at advanced learners’ use of mobile devices for English language study: Insights from interview data"
    expected_author = "Mariusz Kruk"
    
    # Assertions
    if expected_title not in title:
        print(f"FAILED: Expected title '{expected_title}' not found in '{title}'")
        sys.exit(1)
        
    if expected_author not in authors:
        print(f"FAILED: Expected author '{expected_author}' not found in '{authors}'")
        sys.exit(1)
        
    if "Benson" in authors or "Reinders" in authors:
        print(f"FAILED: Hallucinated authors detected: {authors}")
        sys.exit(1)
        
    if confidence < 80:
        print(f"FAILED: Confidence too low: {confidence}")
        sys.exit(1)
        
    print("SUCCESS: Sample X extracted perfectly without hallucination.")

if __name__ == "__main__":
    test_regression_samplex()
