import sys
sys.path.append("backend")

from src.engine import extract_text_from_docx, get_document_metadata
from src.formatter import generate_pdf
import os

def run_test(name, path, out_path):
    print(f"--- Running {name} ---")
    
    if not os.path.exists(path):
        print("Missing file:", path)
        return
        
    print("1. Extracting text blocks (unstructured hi_res)...")
    raw_text = extract_text_from_docx(path)
    
    print("2. Pipelining to LLM semantic chunking...")
    metadata = get_document_metadata(raw_text)
    
    print("3. Generating LaTeX and compiling PDF using raw_text as body...")
    pdf_bytes = generate_pdf(metadata, raw_text)
    with open(out_path, "wb") as f:
        f.write(pdf_bytes)
    print("FINISHED:", out_path)

if __name__ == "__main__":
    run_test("Sample X", "assets/Sample_X_Input.docx", "assets/FINAL_OUTPUT_SAMPLEX.pdf")
