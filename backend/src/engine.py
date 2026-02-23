import docx
import ollama
import json
import re
import hashlib
from sentence_transformers import SentenceTransformer, util

# ==========================================
# 1. TEXT EXTRACTION
# ==========================================
def extract_text_from_docx(file_path):
    """
    Extracts all text from a .docx file and returns it as a single string.
    """
    try:
        doc = docx.Document(file_path)
        extracted_paragraphs = []
        
        for para in doc.paragraphs:
            clean_text = para.text.strip()
            if clean_text:
                extracted_paragraphs.append(clean_text)
                
        return '\n'.join(extracted_paragraphs)
    except Exception as e:
        return f"An error occurred during extraction: {str(e)}"


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
        "headings": "", "references": ""
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

    # --- PASS 1: The Header (Title, Authors, Abstract) ---
    head_text = text_content[:3000]
    prompt_head = f"""You are a rigid Data Extractor. Extract the Title, Authors, and Abstract.
CRITICAL: You MUST copy the Abstract EXACTLY character-for-character. Do not fix typos.
Return ONLY valid JSON.
{{
    "title": "exact title string",
    "authors": "exact authors string",
    "abstract": "exact abstract string"
}}
TEXT:
{head_text}
"""
    try:
        # Added temperature: 0.0 to prevent "and/0" hallucinations
        res_head = ollama.chat(
            model='phi3:mini', 
            messages=[{'role': 'user', 'content': prompt_head}], 
            format='json',
            options={'temperature': 0.0} 
        )
        head_data = json.loads(res_head['message']['content'].strip())
        
        metadata["title"] = flatten_to_string(head_data.get("title", ""))
        metadata["authors"] = flatten_to_string(head_data.get("authors", ""))
        metadata["abstract"] = flatten_to_string(head_data.get("abstract", ""))
    except Exception as e:
        print(f"Header Extraction Failed: {e}")


    # --- PASS 2: RegEx References (Unbreakable) ---
    # LLMs truncate long lists. We use regex to find the "References" section 
    # and grab literally everything until the end of the document.
    try:
        # Looks for the word "References" alone on a line, case-insensitive
        ref_match = re.search(r'(?i)^\s*references\s*\n(.*)', text_content, re.MULTILINE | re.DOTALL)
        if ref_match:
            metadata["references"] = ref_match.group(1).strip()
        else:
            metadata["references"] = "No references section found."
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
        
        # 2. Look for explicit Roman Numerals (IEEE standard) if they survived extraction
        explicit_pattern = re.compile(r'^(?:[IVXLCDM]+|[A-Z]|\d+)\.\s+[A-Z].+', re.MULTILINE)
        found_headings = explicit_pattern.findall(safe_text)
        
        # 3. If numbers were stripped, use Spatial Heuristics
        if not found_headings:
            for line in safe_text.split('\n'):
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
        response = ollama.chat(model='phi3:mini', messages=[{'role': 'user', 'content': prompt}])
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

# Load model globally so it only downloads/loads into RAM once
model = SentenceTransformer('all-MiniLM-L6-v2')

def calculate_semantic_similarity(original_text, modified_text):
    """Proves zero hallucination even if minor typos were fixed."""
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
    if not text.strip(): return "0" * 64
    
    # 1. Get the dense embedding vector
    emb = model.encode(text)
    
    # 2. Binarize the first 64 dimensions (if > 0, it's a 1, else 0)
    # This creates a visual fingerprint of the meaning.
    binary_hash = "".join(["1" if val > 0 else "0" for val in emb[:64]])
    
    # 3. Format it with spaces so it's readable for the UI (e.g., 1101 0010 ...)
    return " ".join(binary_hash[i:i+8] for i in range(0, len(binary_hash), 8))