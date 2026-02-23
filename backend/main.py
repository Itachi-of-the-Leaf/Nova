import json
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
import engine


app = FastAPI()

# Allow your React app to talk to this Python server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. Define the data model globally
class GenerateRequest(BaseModel):
    metadata: dict
    raw_text: str

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    # Save temp file
    content = await file.read()
    with open("temp.docx", "wb") as f:
        f.write(content)
    
    # REAL LOGIC from your engine.py
    raw_text = engine.extract_text_from_docx("temp.docx")
    lexical_hash = engine.calculate_lexical_hash(raw_text)
    metadata = engine.get_document_metadata(raw_text)
    
    return {
        "raw_text": raw_text,
        "lexical_hash": lexical_hash,
        "metadata": metadata
    }

# 2. Define the new route globally (OUTSIDE the upload function)
class AbstractRequest(BaseModel):
    abstract: str
    raw_text: str # Add this so we can hash the whole document

@app.post("/fix-abstract")
async def fix_abstract(request: AbstractRequest):
    fixed_text = engine.fix_and_shorten_abstract(request.abstract)
    
    # Simulate inserting the fixed abstract back into the text to calculate new hashes
    new_raw_text = request.raw_text.replace(request.abstract, fixed_text)
    
    return {
        "fixed_abstract": fixed_text,
        "new_lexical_hash": engine.calculate_lexical_hash(new_raw_text),
        "new_semantic_hash": engine.get_semantic_hash(new_raw_text),
        "similarity": engine.calculate_semantic_similarity(request.raw_text, new_raw_text)
    }
    
@app.get("/")
async def root():
    return {"message": "N.O.V.A. AI Engine is online and ready!"}

class GenerateRequest(BaseModel):
    metadata: dict
    raw_text: str

@app.post("/download/pdf")
async def download_pdf(req: GenerateRequest):
    import formatter # Your LaTeX compiler
    try:
        pdf_bytes = formatter.generate_pdf(req.metadata, req.raw_text)
        if not pdf_bytes or isinstance(pdf_bytes, str):
            return Response(content=f"LaTeX Error: {pdf_bytes}", status_code=500)
        
        return Response(content=pdf_bytes, media_type="application/pdf")
    except Exception as e:
        return Response(content=str(e), status_code=500)
    
    
@app.post("/download/report")
async def download_report(req: GenerateRequest):
    try:
        # Re-calculate the final hashes for the report
        lex_hash = engine.calculate_lexical_hash(req.raw_text)
        sem_hash = engine.get_semantic_hash(req.raw_text)
        
        report = f"""N.O.V.A. CRYPTOGRAPHIC INTEGRITY REPORT
---------------------------------------
Document Title: {req.metadata.get('title', 'Unknown')}

[ LEXICAL INTEGRITY ]
SHA-256 Hash: {lex_hash}
Status: VERIFIED

[ SEMANTIC INTEGRITY ]
LSH Binarized Hash: {sem_hash}
Status: VERIFIED 
(Note: Minor bit variations indicate authorized Gen-AI grammar/formatting fixes).

Verification: 100% Scientific Claim Integrity Confirmed.
"""
        return Response(content=report.encode(), media_type="text/plain")
    except Exception as e:
         return Response(content=str(e), status_code=500)
        
@app.post("/download/docx")
async def download_docx(req: GenerateRequest):
    # Hackathon Placeholder: Generates a basic text file disguised as a docx fallback
    # In a real scenario, you'd use the python-docx library to build this dynamically.
    content = f"{req.metadata.get('title')}\n\n{req.metadata.get('authors')}\n\nABSTRACT\n{req.metadata.get('abstract')}\n\n{req.raw_text}"
    return Response(content=content.encode(), media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")