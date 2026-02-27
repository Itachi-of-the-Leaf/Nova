import urllib.request
import urllib.parse
import json
import re
import concurrent.futures

def verify_single_citation(citation):
    """Hits the Crossref API to verify and deterministically reconstruct the citation."""
    clean_citation = citation.strip()
    if len(clean_citation) < 15:
        return citation  # Too short to be a real citation, return as-is
    
    # URL encode the citation string for the query
    encoded_query = urllib.parse.quote(clean_citation)
    url = f"https://api.crossref.org/works?query.bibliographic={encoded_query}&rows=1&select=title,DOI,score,author,published-print,published-online,container-title"
    
    # Crossref asks for a polite User-Agent
    req = urllib.request.Request(url, headers={'User-Agent': 'NOVA_Prototype/1.0 (mailto:prototype@nova.local)'})
    
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            items = data.get("message", {}).get("items", [])
            
            if items:
                top_hit = items[0]
                score = top_hit.get("score", 0)
                
                # A score > 35 generally means Crossref found a highly accurate match
                if score > 35:
                    doi = top_hit.get("DOI", "No DOI")
                    title = top_hit.get("title", [""])[0]
                    author_list = top_hit.get("author", [])
                    authors = ", ".join([f"{a.get('given', '')} {a.get('family', '')}".strip() for a in author_list])
                    
                    year = ""
                    pub = top_hit.get("published-print") or top_hit.get("published-online")
                    if pub and "date-parts" in pub and pub["date-parts"]:
                        year = pub["date-parts"][0][0]
                        
                    venue = top_hit.get("container-title", [""])[0]
                    
                    # Deterministically construct the confirmed reference, destroying original messy/hallucinated data
                    constructed = f"{authors}. \"{title}.\" {venue} ({year})."
                    if doi and doi != "No DOI":
                        constructed += f" https://doi.org/{doi}"
                    
                    return f"✅ [VERIFIED | DOI: {doi}]\n{constructed}"
                else:
                    return f"⚠️ [LOW CONFIDENCE | Possible Hallucination]\n{clean_citation}"
            else:
                return f"❌ [NOT FOUND IN CROSSREF]\n{clean_citation}"
                
    except Exception as e:
        return f"❓ [API TIMEOUT / ERROR]\n{clean_citation}"

def verify_references_block(references_text):
    """Refined splitter for APA/MLA (Name-Year) and Numbered lists."""
    if not references_text or "No references" in references_text:
        return references_text
    
    # NEW REGEX: Splits by:
    # 1. Numbered items: [1] or 1.
    # 2. APA Items: Newline followed by an Uppercase Name and a (Year)
    # 3. Double newlines
    raw_citations = re.split(r'\n(?=\[\d+\]|\d+\.|[A-Z][a-z]+,?\s+[A-Z]\.?\s*\(?\d{4}\)?)| \n\n+', references_text)
    
    citations = [c.strip() for c in raw_citations if len(c.strip()) > 15]
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(verify_single_citation, citations))
    
    return "\n\n".join(results)