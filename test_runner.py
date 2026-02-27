import os
import sys
sys.path.append("backend")
import json
import logging
from src.engine import extract_text_from_docx

logging.basicConfig(level=logging.INFO, format="%(message)s")

def runner():
    files = ["assets/Sample_3_Input.docx", "assets/Sample_X_Input.docx"]
    for file in files:
        logging.info(f"--- Processing {file} ---")
        try:
            raw_text = extract_text_from_docx(file)
            from src.engine import get_document_metadata
            metadata = get_document_metadata(raw_text)
            
            from src.formatter import generate_pdf
            pdf_bytes = generate_pdf(metadata, raw_text)
            
            base_name = os.path.basename(file).split(".")[0]
            json_out = f"assets/{base_name}_output.json"
            pdf_out = f"assets/{base_name}_test_output.pdf"
            
            with open(json_out, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2)
            logging.info(f"Saved metadata to {json_out}")
            
            with open(pdf_out, "wb") as f:
                f.write(pdf_bytes)
            logging.info(f"Saved PDF to {pdf_out}")
            
        except Exception as e:
            logging.error(f"Failed {file}: {e}")

if __name__ == "__main__":
    runner()
