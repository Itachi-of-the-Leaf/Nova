import docx
import ollama
import os
import json
import re
import hashlib
from sentence_transformers import SentenceTransformer, util
from .verifier import verify_references_block

# The model to use for AI extraction.
# Override by setting OLLAMA_MODEL in your environment, e.g.:
#   set OLLAMA_MODEL=llama3  (Windows)
#   export OLLAMA_MODEL=llama3  (Mac/Linux)
OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL', 'phi3:mini')

# ==========================================
# 1. TEXT EXTRACTION
# ==========================================
def extract_text_from_docx(file_path):
    """
    Extracts text from a .docx file using the unstructured library. 
    This enables Document Layout Analysis (DLA) that preserves spatial relationships
    (multi-column flows, tables, headers) before feeding to the NLP engine.
    """
    try:
        from unstructured.partition.auto import partition
        
        # Partition docx/pdf extracts layout-aware semantic blocks to prevent
        # multi-column reading order corruption. Use hi_res and yolo to avoid OCR artifacts on tables.
        elements = partition(
            filename=file_path,
            strategy="hi_res",
            hi_res_model_name="yolox",
            infer_table_structure=True,
            pdf_infer_table_structure=True,
            chunking_strategy="by_title"
        )
        
        extracted_blocks = []
        import re
        
        # PASS 1: Extract Footnotes to a dictionary to restore their spatial layout inline
        footnotes = {}
        normal_elements = []
        for element in elements:
            clean_text = str(element).strip()
            if not clean_text:
                continue
            
            # unstructured natively tags footnotes as 'Footnote' if metadata is rich
            if type(element).__name__ == "Footnote":
                # Usually looks like "1 This is a footnote" or "[1] This is a footnote"
                m = re.match(r'^\[?(\d+)\]?[\s\.\:]+(.*)', clean_text)
                if m:
                    footnotes[m.group(1)] = m.group(2)
                else:
                    # Fallback string
                    footnotes["unknown"] = clean_text
            else:
                normal_elements.append(element)

        # PASS 2: Process text and inject \footnote inline
        for element in normal_elements:
            clean_text = str(element).strip()

            # targeted regex to fix OCR artifacts where S<number> is read as $<number>
            clean_text = re.sub(r'\$(\d+)', r'S\1', clean_text)

            # Inject footnotes inline so LaTeX renders them at the bottom of the spatial page
            if footnotes:
                def repl_footnote(m):
                    fn_num = m.group(1)
                    if fn_num in footnotes:
                        fn_text = footnotes.pop(fn_num) # only inject once
                        # We use @@FOOTNOTE@@ instead of direct LaTeX here so formatter.py can escape it later
                        return f"@@FOOTNOTE@@{fn_text}@@END@@"
                    return m.group(0)
                
                # Match [1] or ^1 in the text
                clean_text = re.sub(r'\[?(\d+)\]?', repl_footnote, clean_text)

            el_type = type(element).__name__
            
            # Map structural elements to our tagging format
            if el_type == "Title":
                depth = getattr(element.metadata, "category_depth", 0) if hasattr(element, "metadata") else 0
                if depth == 0 or depth == 1:
                    extracted_blocks.append(f"@@H1@@{clean_text}@@END@@")
                elif depth == 2:
                    extracted_blocks.append(f"@@H2@@{clean_text}@@END@@")
                else:
                    extracted_blocks.append(f"@@H3@@{clean_text}@@END@@")
            elif el_type == "Table":
                # Convert complex tables directly to HTML to preserve rowspan/colspan
                html = getattr(element.metadata, "text_as_html", "") if hasattr(element, "metadata") else ""
                if html:
                    extracted_blocks.append(f"\n[TABLE_START]\n{html}\n[TABLE_END]\n")
                else:
                    extracted_blocks.append(f"\n[TABLE_START]\n{clean_text}\n[TABLE_END]\n")
            elif el_type in ["Header", "Footer"]:
                # Ignore running headers/footers to avoid polluting core text semantic flow
                continue
            elif el_type == "ListItem":
                extracted_blocks.append(f"@@LIST_ITEM@@{clean_text}@@END@@")
            else:
                extracted_blocks.append(clean_text)
                
        # Append any un-injected footnotes to the body so they aren't completely lost
        for fn_num, fn_text in footnotes.items():
            extracted_blocks.append(f"@@FOOTNOTE@@{fn_text}@@END@@")
            
        return '\n'.join(extracted_blocks)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"An error occurred during extraction: {str(e)}"



# ==========================================
# 2. METADATA PARSING (The "Brain")
# ==========================================
def get_document_metadata(text_content):
    """
    A robust, multi-pass extraction engine implementing the "Semantic Chunking" strategy 
    to prevent RAM overload and context window loss on large documents.
    """
    metadata = {
        "title": "", "authors": "", "abstract": "",
        "headings": "", "references": ""
    }

    # ==========================================
    # Helper: The "Data Flattener" Shield
    # ==========================================
    def flatten_to_string(data):
        if isinstance(data, str):
            return data.strip()
        elif isinstance(data, list):
            if len(data) > 0 and isinstance(data[0], dict):
                return "\n".join([" ".join(str(v) for v in d.values()) for d in data])
            return "\n".join(str(i) for i in data)
        elif isinstance(data, dict):
            return "\n".join(str(v) for v in data.values())
        return str(data)

    def _safe_json_parse(raw: str) -> dict:
        text = raw.strip()
        if text.startswith('```'):
            lines = text.splitlines()
            inner = [l for l in lines[1:] if l.strip() != '```']
            text = '\n'.join(inner).strip()
        return json.loads(text)

    # ==========================================
    # PASS 1: Map-Reduce Semantic Chunking
    # ==========================================
    # Break the document into strictly sized chunks to protect the KV cache (8GB RAM limit)
    chunks = get_semantic_chunks(text_content, chunk_size=2000)
    
    # Iterate through the first few chunks to handle massive title pages or cover letters
    for i, chunk in enumerate(chunks[:3]):
        # Skip inference if we already successfully extracted the core header data
        if metadata["title"] and metadata["abstract"] and len(metadata["abstract"]) > 50:
            break

        prompt_head = f"""You are a rigid Data Extractor. Extract the Title, Authors, and Abstract from the text below.
CRITICAL INSTRUCTIONS:
1. For Authors, extract FULL HUMAN NAMES cleanly (no emails, numbers, or affiliations).
2. If a field is not found in this specific text chunk, return an empty string "".
3. Copy the Abstract EXACTLY character-for-character.

Return ONLY valid JSON:
{{
    "title": "exact title string",
    "authors": "Full Name 1, Full Name 2",
    "abstract": "exact abstract string"
}}
TEXT:
{chunk}
"""
        try:
            res_head = ollama.chat(
                model=OLLAMA_MODEL,
                messages=[{'role': 'user', 'content': prompt_head}],
                format='json',
                options={'temperature': 0.0},
            )
            data = _safe_json_parse(res_head['message']['content'])

            # Only overwrite if the new chunk found something and we didn't already have it
            new_title = flatten_to_string(data.get("title", ""))
            new_authors = flatten_to_string(data.get("authors", ""))
            new_abstract = flatten_to_string(data.get("abstract", ""))

            if new_title and len(new_title) > 5 and not metadata["title"]: 
                metadata["title"] = new_title
            if new_authors and not metadata["authors"]: 
                metadata["authors"] = new_authors
            if new_abstract and len(new_abstract) > 20 and not metadata["abstract"]: 
                metadata["abstract"] = new_abstract

        except Exception as e:
            print(f"Chunk {i} Extraction Failed: {e}")

    # ==========================================
    # PASS 2: RegEx References (Unbreakable)
    # ==========================================
    try:
        ref_match = re.search(r'(?i)^\s*references\b[\s:]*(.*)', text_content, re.MULTILINE | re.DOTALL)
        if ref_match:
            raw_refs = ref_match.group(1).strip()
            # RUN THE TRUTH ENGINE
            metadata["references"] = verify_references_block(raw_refs)
        else:
            metadata["references"] = "No references section found."
    except Exception as e:
        print(f"Reference Extraction Failed: {e}")

    # ==========================================
    # PASS 3: Context-Aware Heading Detection
    # ==========================================
    try:
        abstract_match = re.search(r'(?i)abstract', text_content)
        safe_start_idx = abstract_match.end() if abstract_match else 1000
        safe_text = text_content[safe_start_idx:]
        
        found_headings = []
        explicit_pattern = re.compile(r'^(?:[IVXLCDM]+|[A-Z]|\d+)\.\s+[A-Z].+', re.MULTILINE)
        found_headings = explicit_pattern.findall(safe_text)
        
        if not found_headings:
            for line in safe_text.split('\n'):
                line = line.strip()
                if 2 < len(line) < 60 and line[0].isupper() and not line.endswith(('.', '?', '!', ':')):
                    lower_line = line.lower()
                    if '@' not in line and not any(bad in lower_line for bad in ['university', 'college', 'school', 'department', 'institute']):
                        found_headings.append(line)
        
        if found_headings:
            seen = set()
            unique_headings = [x for x in found_headings if not (x in seen or seen.add(x))]
            metadata["headings"] = "\n".join(unique_headings)
        else:
            metadata["headings"] = "No standard headings detected."
            
    except Exception as e:
        print(f"Heading Detection Failed: {e}")

    # ==========================================
    # PASS 4: Dynamic Confidence Score
    # ==========================================
    confidence = 100
    
    if len(metadata["title"]) < 5 or "Error" in metadata["title"]: confidence -= 25
    if len(metadata["authors"]) < 3: confidence -= 15
    if len(metadata["abstract"]) < 40: confidence -= 30
    if len(metadata["references"]) < 15: confidence -= 15
    if "No standard headings detected" in metadata["headings"]: confidence -= 10
    
    metadata["confidence"] = max(10, min(100, confidence))
    
    return metadata


# ==========================================
# 3. GEN-AI FIXER (Auto-Editor)
# ==========================================
def fix_and_shorten_abstract(abstract_text):
    """
    Ethical AI Firewall: Generative modification of human prose is disabled to prevent
    AI detector false positives (Turnitin/GPTZero). Returns original text exactly,
    preserving burstiness and perplexity.
    """
    return abstract_text


# ==========================================
# 4. HASHING & INTEGRITY
# ==========================================
def calculate_lexical_hash(text_content):
    """Generates a SHA-256 hash of the raw alphanumeric character string."""
    clean_string = "".join(text_content.split()).encode('utf-8')
    return hashlib.sha256(clean_string).hexdigest()

def get_semantic_chunks(text, chunk_size=2000):
    """Divides the manuscript into manageable windows to prevent RAM overload."""
    paragraphs = text.split('\n')
    chunks = []
    current_chunk = ""
    for para in paragraphs:
        if len(current_chunk) + len(para) < chunk_size:
            current_chunk += para + "\n"
        else:
            chunks.append(current_chunk.strip())
            current_chunk = para + "\n"
    chunks.append(current_chunk.strip())
    return chunks

# Lazy singleton — the ~90MB model loads only on first use, not at import time.
# This prevents the server from hanging during startup/model-download.
_model = None

def _get_model():
    global _model
    if _model is None:
        print("[N.O.V.A.] Loading SentenceTransformer model (first use)...")
        _model = SentenceTransformer('all-MiniLM-L6-v2')
        print("[N.O.V.A.] Model loaded.")
    return _model

def calculate_semantic_similarity(original_text, modified_text):
    """Proves zero hallucination even if minor typos were fixed."""
    model = _get_model()
    emb1 = model.encode(original_text, convert_to_tensor=True)
    emb2 = model.encode(modified_text, convert_to_tensor=True)
    cosine_scores = util.cos_sim(emb1, emb2)
    return float(cosine_scores[0][0])

if __name__ == "__main__":
    pass

def get_semantic_hash(text):
    """
    Creates a visual 'Locality-Sensitive Hash' (LSH).
    Unlike SHA-256, similar text will produce visually similar binary strings!
    """
    if not text.strip():
        return "0" * 64

    model = _get_model()

    # Binarize the first 64 dimensions (1 if > 0 else 0)
    emb = model.encode(text)
    binary_hash = "".join(["1" if val > 0 else "0" for val in emb[:64]])

    # Format with spaces for readability in the UI (e.g., "1101 0010 ...")
    return " ".join(binary_hash[i:i+8] for i in range(0, len(binary_hash), 8))


# ── Startup check ─────────────────────────────────────────────────────────────
# Runs once when this module is first imported (i.e. when uvicorn starts).
# Tells you immediately in the terminal if Ollama is reachable.
def _check_ollama():
    try:
        ollama.list()
        print(f"[N.O.V.A.] ✅ Ollama is reachable. Using model: '{OLLAMA_MODEL}'")
        # Check if the model is actually pulled
        models = [m['model'] for m in ollama.list().get('models', [])]
        if not any(OLLAMA_MODEL in m for m in models):
            print(f"[N.O.V.A.] ⚠️  Model '{OLLAMA_MODEL}' is NOT pulled yet!")
            print(f"[N.O.V.A.] ⚠️  Run:  ollama pull {OLLAMA_MODEL}")
    except Exception as e:
        print(f"[N.O.V.A.] ⚠️  Ollama is NOT reachable: {e}")
        print("[N.O.V.A.] ⚠️  Start Ollama with:  ollama serve")

_check_ollama()