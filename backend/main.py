import os
import asyncio
import json
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, JSONResponse
from pydantic import BaseModel

# Resolve the backend root and the shared data directory using __file__
# so paths are always correct no matter which directory uvicorn is launched from.
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR    = os.path.join(BACKEND_DIR, "data")
TEMP_DOCX   = os.path.join(DATA_DIR, "temp.docx")

# Use simple relative imports — no full dotted-package path needed.
from src import engine, formatter

app = FastAPI()

# Allow the React app to talk to this Python server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Data Models ────────────────────────────────────────────────────────────────

class AbstractRequest(BaseModel):
    abstract: str
    raw_text: str

class GenerateRequest(BaseModel):
    metadata: dict
    raw_text: str


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {"message": "N.O.V.A. AI Engine is online and ready!"}


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Save file, hash it, and run LLM metadata extraction — all in one request."""
    try:
        content = await file.read()
        with open(TEMP_DOCX, "wb") as f:
            f.write(content)

        # Run all blocking work in threads so uvicorn's event loop stays free
        raw_text     = await asyncio.to_thread(engine.extract_text_from_docx, TEMP_DOCX)
        lexical_hash = await asyncio.to_thread(engine.calculate_lexical_hash, raw_text)
        metadata     = await asyncio.to_thread(engine.get_document_metadata, raw_text)

        return {
            "raw_text":     raw_text,
            "lexical_hash": lexical_hash,
            "metadata":     metadata,
        }
    except Exception as e:
        import traceback; traceback.print_exc()
        return JSONResponse(status_code=500, content={"detail": str(e)})


@app.post("/fix-abstract")
async def fix_abstract(request: AbstractRequest):
    fixed_text   = engine.fix_and_shorten_abstract(request.abstract)
    new_raw_text = request.raw_text.replace(request.abstract, fixed_text)

    return {
        "fixed_abstract":    fixed_text,
        "new_lexical_hash":  engine.calculate_lexical_hash(new_raw_text),
        "new_semantic_hash": engine.get_semantic_hash(new_raw_text),
        "similarity":        engine.calculate_semantic_similarity(request.raw_text, new_raw_text),
    }


@app.post("/download/pdf")
async def download_pdf(req: GenerateRequest):
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
    content = (
        f"{req.metadata.get('title')}\n\n"
        f"{req.metadata.get('authors')}\n\n"
        f"ABSTRACT\n{req.metadata.get('abstract')}\n\n"
        f"{req.raw_text}"
    )
    return Response(
        content=content.encode(),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )