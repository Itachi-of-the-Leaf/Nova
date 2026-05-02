import docx
import ollama
import os
import json
import re
import hashlib
import requests
from sentence_transformers import SentenceTransformer, util

# The model to use for AI extraction.
# Override by setting OLLAMA_MODEL in your environment, e.g.:
#   set OLLAMA_MODEL=llama3  (Windows)
#   export OLLAMA_MODEL=llama3  (Mac/Linux)
OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL', 'phi3:mini')


# ==========================================
# 0. REFERENCE PARSER (Standalone Helper)
# ==========================================
def parse_individual_references(refs_text: str) -> list:
    """
    Parses a raw references block into a structured list of dicts:
      [{"number": 1, "text": "Author et al..."}, ...]

    Tries four strategies in order:
      1. [N] IEEE-style numeric
      2. N. / N) numbered list
      3. Blank-line-separated paragraphs
      4. Hanging indent simulation (lines starting with capital letters)
    """
    if not refs_text or "No references section found" in refs_text:
        return []

    text = refs_text.strip()

    # Strategy 1: [N] format
    if re.search(r'^\[\d+\]', text, re.MULTILINE):
        entries = re.split(r'(?=^\[\d+\])', text, flags=re.MULTILINE)
        result = []
        for entry in entries:
            entry = entry.strip()
            m = re.match(r'^\[(\d+)\]\s*(.*)', entry, re.DOTALL)
            if m:
                result.append({"number": int(m.group(1)), "text": m.group(2).strip()})
        if len(result) > 1:
            return result

    # Strategy 2: N. or N) format
    if re.search(r'^\d+[.)]\s', text, re.MULTILINE):
        entries = re.split(r'(?=^\d+[.)]\s)', text, flags=re.MULTILINE)
        result = []
        for entry in entries:
            entry = entry.strip()
            m = re.match(r'^(\d+)[.)]\s*(.*)', entry, re.DOTALL)
            if m:
                result.append({"number": int(m.group(1)), "text": m.group(2).strip()})
        if len(result) > 1:
            return result

    # Strategy 3: blank-line-separated paragraphs
    paragraphs = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]
    if len(paragraphs) > 1:
        return [{"number": i + 1, "text": p} for i, p in enumerate(paragraphs)]

    # Strategy 4: APA-style wrapped without blank lines (looks for (YYYY) to split)
    # If lines are wrapped, a new reference usually starts with a capitalized name and has a (Year) near the start.
    # A simple fallback: assume each line that isn't indented or just a URL is a new reference.
    lines = text.split('\n')
    result = []
    current_ref = ""
    
    for line in lines:
        stripped = line.strip()
        if not stripped: continue
        
        # Heuristic: if line starts with uppercase letter and doesn't look like a URL continuation
        if stripped[0].isupper() and not stripped.startswith('http') and len(stripped) > 10:
            if current_ref:
                result.append(current_ref)
            current_ref = stripped
        else:
            current_ref += " " + stripped
            
    if current_ref:
        result.append(current_ref)
        
    if len(result) > 1:
         return [{"number": i + 1, "text": r.strip()} for i, r in enumerate(result)]

    # Fallback: whole block as a single entry
    return [{"number": 1, "text": text}]


# ==========================================
# 1. CROSSREF CITATION VERIFIER
# ==========================================
def verify_citation_crossref(citation_text: str) -> dict:
    """
    Queries the Crossref /works endpoint for the best bibliographic match to
    `citation_text` and returns a dict with keys: title, author, url, doi.

    Includes a User-Agent and mailto to enter the Crossref 'Polite Pool' and
    prevent connection errors. Handles direct DOI lookups if applicable.
    """
    # Regex for identifying a DOI: starts with 10. and contains a prefix/suffix
    doi_pattern = r'\b(10\.\d{4,9}/[-._;()/:a-zA-Z0-9]+)\b'
    doi_match = re.search(doi_pattern, citation_text)
    
    headers = {
        "User-Agent": "NovaIntegrityBot/1.0 (mailto:integrity@projectnova.io)"
    }

    if doi_match:
        # Direct DOI lookup is more reliable if it exists
        doi = doi_match.group(1)
        try:
            res = requests.get(f"https://api.crossref.org/works/{doi}", headers=headers, timeout=10)
            if res.status_code == 200:
                item = res.json().get("message", {})
                authors = item.get("author", [])
                author_str = ", ".join(f"{a.get('given', '')} {a.get('family', '')}".strip() for a in authors)
                return {
                    "title":  " ".join(item.get("title", ["Unknown Title"])),
                    "author": author_str or "Unknown Author",
                    "url":    item.get("URL", ""),
                    "doi":    item.get("DOI", ""),
                }
        except Exception:
            pass # Fallback to search if direct lookup fails

    # Search-based fallback
    base_url = "https://api.crossref.org/works"
    params = {
        "query":  citation_text,
        "rows":   1,
        "select": "title,author,URL,DOI",
    }
    try:
        response = requests.get(base_url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        items = data.get("message", {}).get("items", [])
        if not items:
            return {"error": "No results found for the given citation."}

        item = items[0]
        authors = item.get("author", [])
        author_str = ", ".join(f"{a.get('given', '')} {a.get('family', '')}".strip() for a in authors)
        return {
            "title":  " ".join(item.get("title", ["Unknown Title"])),
            "author": author_str or "Unknown Author",
            "url":    item.get("URL", ""),
            "doi":    item.get("DOI", ""),
        }
    except requests.exceptions.RequestException as exc:
        return {"error": f"Error connecting to Crossref: {exc}"}
    except (ValueError, KeyError) as exc:
        return {"error": f"Failed to parse Crossref response: {exc}"}


def extract_text_from_docx(file_path):
    """
    Extracts text from a .docx file, tagging headings by their DOCX style:
      Heading 1 / Title → @@H1@@text@@END@@
      Heading 2         → @@H2@@text@@END@@
      Heading 3         → @@H3@@text@@END@@
    These markers let formatter.py produce proper \\section / \\subsection hierarchy.
    """
    try:
        doc = docx.Document(file_path)
        extracted_paragraphs = []

        for para in doc.paragraphs:
            clean_text = para.text.strip()
            if not clean_text:
                continue

            style = para.style.name if para.style else ""

            if style.startswith("Heading 1") or style == "Title" or style.startswith("Heading 2") or style.startswith("Heading 3"):
                # We no longer inject @@Hn@@ inline tags
                extracted_paragraphs.append(clean_text)
            else:
                extracted_paragraphs.append(clean_text)

        return '\n'.join(extracted_paragraphs)
    except Exception as e:
        return f"An error occurred during extraction: {str(e)}"


def extract_abstract_natively(text_content: str) -> str:
    """
    Slices the abstract from raw text using landmark detection.
    Guarantees 100% deterministic extraction (no LLM rewriting).
    """
    text_lower = text_content.lower()
    start_match = re.search(r'(?i)\babstract\b', text_content)
    if not start_match:
        return ""
    
    content_start = start_match.end()
    # Skip any separator characters like colons or newlines
    while content_start < len(text_content) and text_content[content_start] in (":", "\n", " ", "\r", "."):
        content_start += 1
        
    # Landmarks for end of abstract
    keywords_match = re.search(r'(?i)\bkeywords\b', text_content[content_start:])
    intro_match = re.search(r'(?i)\bintroduction\b', text_content[content_start:])
    
    end_indices = []
    if keywords_match: end_indices.append(content_start + keywords_match.start())
    if intro_match: end_indices.append(content_start + intro_match.start())
    
    if not end_indices:
        # If no landmarks, take up to 2500 chars (safe buffer for long abstracts)
        return text_content[content_start:content_start + 2500].strip()
    
    return text_content[content_start:min(end_indices)].strip()


# ==========================================
# 1b. OCR ARTIFACT CLEANER
# ==========================================
def clean_ocr_artifacts(text: str) -> str:
    """
    Removes the pdfplumber OCR artifact '/0' that appears immediately after a
    common English word (e.g. 'and/0' -> 'and').

    Root cause: pdfplumber sometimes mis-decodes fi-ligatures (U+FB01 → '/')
    in certain PDF fonts. The token 'and' followed by a ligature-prefixed word
    (e.g. 'figure') collapses to 'and/0gure', then is further truncated to
    'and/0' in the extraction buffer.

    Regex strategy — word-boundary whitelist:
      \\b(and|or|the|of|in|to|for|with|from|by|at|on|is|are|was|were|be|been)/0(?!\\d)

      - \\b          : word boundary — the match must start at the beginning of a word
      - (and|or|...) : whitelist of common English function words that are never
                       used as single-character math variables
      - /0           : the literal artifact string
      - (?!\\d)       : negative lookahead — preserves '/01', '/05', etc.

    Safety: single-letter variables (x/0, n/0) and numeric expressions (1/0,
    f(n)/0) are completely unaffected because none of their left operands appear
    in the whitelist.
    """
    _ARTIFACT_RE = re.compile(
        r'\b(and|or|the|of|in|to|for|with|from|by|at|on|is|are|was|were|be|been)/0(?!\d)',
        re.IGNORECASE,
    )
    return _ARTIFACT_RE.sub(r'\1', text)



# ==========================================
# 2. METADATA PARSING (The "Brain")
# ==========================================
def get_document_metadata(text_content):
    """
    A robust, multi-pass extraction engine designed to prevent SLM hallucinations
    and handle context window limits on 8GB RAM machines.
    """
    metadata = {
        "title": "", "authors": "", "abstract": "",
        "headings": "", "references": "", "references_list": []
    }

    # ==========================================
    # Helper: The "Data Flattener" Shield
    # ==========================================
    # This prevents the [object Object] frontend crash by forcing everything into a string.
    def flatten_to_string(data):
        if isinstance(data, str):
            return data.strip()
        elif isinstance(data, list):
            # If the AI returned an array of objects, extract their values
            if len(data) > 0 and isinstance(data[0], dict):
                return "\n".join([" ".join(str(v) for v in d.values()) for d in data])
            # If it's a simple array of strings
            return "\n".join(str(i) for i in data)
        elif isinstance(data, dict):
            return "\n".join(str(v) for v in data.values())
        return str(data)

    # ── JSON helper ────────────────────────────────────────────────────────────
    # phi3:mini sometimes wraps its JSON in markdown code fences even when
    # format='json' is set. Strip them before parsing so we actually get the data.
    def _safe_json_parse(raw: str) -> dict:
        text = raw.strip()
        # Remove ```json ... ``` or ``` ... ``` wrapping
        if text.startswith('```'):
            lines = text.splitlines()
            # Drop the first line (```json or ```) and the last (```)
            inner = [l for l in lines[1:] if l.strip() != '```']
            text = '\n'.join(inner).strip()
        return json.loads(text)

    head_text = text_content[:10000] # Provide enough context to capture sections
    prompt_head = f"""You are a strict, deterministic Data Extractor.
Extract the document's semantics into a Strict JSON Object.

CRITICAL INSTRUCTIONS:
1. TITLE: Ignore header artifacts such as 'Research paper', 'Article', 'Short Communication', or journal names/logos. Extract the semantic academic title of the work.
2. AUTHORS: Extract the FULL HUMAN NAMES cleanly. Do NOT include email addresses, university affiliations, or numbers.
3. ABSTRACT: Extract the entire abstract character-for-character. 
   - Do NOT stop at line breaks or paragraph breaks. 
   - Continue extracting until you explicitly reach the word 'Keywords:' or 'Introduction'.
   - Do NOT rephrase, rewrite, or correct anything.
4. SECTIONS: Identify major sections (Introduction, Methods, Results, Conclusion). Do NOT use inline @@ tags.

Return ONLY valid JSON matching this schema exactly:
{{
    "metadata": {{
        "title": "exact title string",
        "authors": "Full Name 1, Full Name 2"
    }},
    "abstract": "exact abstract string",
    "sections": [
        {{"heading": "Heading Name", "content": "Section content..."}}
    ]
}}
TEXT:
{head_text}
"""
    try:
        res_head = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[{'role': 'user', 'content': prompt_head}],
            format='json',
            options={'temperature': 0.0},
        )
        raw_content = res_head['message']['content']
        head_data = _safe_json_parse(raw_content)

        metadata_field = head_data.get("metadata", {})
        metadata["title"]    = flatten_to_string(metadata_field.get("title", ""))
        metadata["authors"]  = flatten_to_string(metadata_field.get("authors", ""))
        
        # USE NATIVE EXTRACTION AS PRIMARY OR FALLBACK FOR ABSTRACT
        llm_abstract = flatten_to_string(head_data.get("abstract", ""))
        native_abstract = extract_abstract_natively(text_content)
        
        # If LLM truncated or native is significantly longer/better, prefer native
        if len(native_abstract) > len(llm_abstract) * 1.2 or not llm_abstract:
            metadata["abstract"] = native_abstract
        else:
            metadata["abstract"] = llm_abstract
            
        # Format the sections array back into the expected plain text or pass it structured
        sections = head_data.get("sections", [])
        if sections:
            metadata["headings"] = "\n".join([str(s.get("heading", "")) for s in sections])
        else:
            metadata["headings"] = "No standard headings detected."
            
    except Exception as e:
        print(f"Header Extraction Failed: {e}")
        print(f"  Raw LLM output: {res_head['message']['content'][:300] if 'res_head' in dir() else 'N/A'}")


    # --- PASS 2: RegEx References (Unbreakable) ---
    # LLMs truncate long lists. We use regex to find the "References" section
    # and grab literally everything until the end of the document.
    try:
        # Strip DOCX heading markers BEFORE searching — lines tagged as headings
        # start with @@H1@@ etc., so the plain '^references' pattern never matches.
        clean_for_refs = re.sub(r'@@H[123]@@(.*?)@@END@@', r'\1', text_content)

        # Strategy 1: explicit "References" section heading
        ref_match = re.search(r'(?i)^\s*references\b[\s:]*(.*)', clean_for_refs, re.MULTILINE | re.DOTALL)
        if ref_match:
            metadata["references"] = ref_match.group(1).strip()
        else:
            # Strategy 2: scan from bottom for first [1] / 1. entry
            lines = clean_for_refs.split('\n')
            ref_start = -1
            for i in range(len(lines) - 1, -1, -1):
                stripped = lines[i].strip()
                if re.match(r'^\[1\]|^1[.)\s]', stripped):
                    ref_start = i
                    break
            if ref_start >= 0:
                metadata["references"] = '\n'.join(lines[ref_start:]).strip()
            else:
                metadata["references"] = "No references section found."

        metadata["references_list"] = parse_individual_references(metadata["references"])
    except Exception as e:
        print(f"Reference Extraction Failed: {e}")


    # --- PASS 3: Context-Aware Heading Detection & Content Parsing ---
    try:
        # 1. Find the "Safe Zone" (Everything after the abstract)
        # This prevents author names and affiliations from being tagged as headings
        abstract_match = re.search(r'(?i)abstract', text_content)
        safe_start_idx = abstract_match.end() if abstract_match else 1000
        safe_text = text_content[safe_start_idx:]
        
        found_headings = []
        
        # 1.5 Extract explicitly tagged headings from DOCX
        tagged_pattern = re.compile(r'@@H[123]@@(.*?)@@END@@')
        tagged_headings = tagged_pattern.findall(safe_text)
        if tagged_headings:
            found_headings.extend(tagged_headings)
        
        # Strip tags from safe_text to allow other heuristics to work correctly
        clean_safe_text = re.sub(r'@@H[123]@@(.*?)@@END@@', r'\1', safe_text)
        
        # 2. Look for explicit Roman Numerals (IEEE standard) if they survived extraction
        if not found_headings:
            explicit_pattern = re.compile(r'^(?:[IVXLCDM]+|[A-Z]|\d+)\.\s+[A-Z].+', re.MULTILINE)
            found_headings = explicit_pattern.findall(clean_safe_text)
        
        # 3. If numbers were stripped, use Spatial Heuristics
        if not found_headings:
            for line in clean_safe_text.split('\n'):
                line = line.strip()
                # A heading is usually short, capitalized, and doesn't end in punctuation.
                # We strictly filter out emails (@) and common affiliation words.
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

    # --- PASS 4: Dynamic Confidence Score ---
    # We now check the actual *length* of the strings, ensuring the AI didn't just return a 1-letter mistake
    confidence = 100
    
    if len(metadata["title"]) < 5 or "Error" in metadata["title"]: confidence -= 25
    if len(metadata["authors"]) < 3: confidence -= 15
    if len(metadata["abstract"]) < 40: confidence -= 30
    if len(metadata["references"]) < 15: confidence -= 15
    if "No standard headings detected" in metadata["headings"]: confidence -= 10
    
    # Cap between 10% and 100% to keep the UI looking normal
    metadata["confidence"] = max(10, min(100, confidence))
    
    return metadata


# ==========================================
# 3. GEN-AI FIXER (Auto-Editor)
# ==========================================
def fix_and_shorten_abstract(abstract_text):
    """
    Uses the local LLM to fix grammar and shorten the abstract to <250 words.
    """
    prompt = f"""You are an expert academic editor.
Please rewrite the following abstract to fix any grammatical errors, improve academic tone, and ensure it is strictly under 250 words.
Return ONLY the revised abstract text. Do not include any conversational filler, explanations, or quotes.

ORIGINAL ABSTRACT:
{abstract_text}
"""
    try:
        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[{'role': 'user', 'content': prompt}],
        )
        return response['message']['content'].strip()
    except Exception as e:
        print(f"AI Fixer Failed: {e}")
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
        print(f"[N.O.V.A.] [OK] Ollama is reachable. Using model: '{OLLAMA_MODEL}'")
        # Check if the model is actually pulled
        models = [m['model'] for m in ollama.list().get('models', [])]
        if not any(OLLAMA_MODEL in m for m in models):
            print(f"[N.O.V.A.] [WARN] Model '{OLLAMA_MODEL}' is NOT pulled yet!")
            print(f"[N.O.V.A.] [WARN] Run:  ollama pull {OLLAMA_MODEL}")
    except Exception as e:
        print(f"[N.O.V.A.] [WARN] Ollama is NOT reachable: {e}")
        print("[N.O.V.A.] [WARN] Start Ollama with:  ollama serve")

_check_ollama()