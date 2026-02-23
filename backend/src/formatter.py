import os
import subprocess

# Anchor all LaTeX-related files to backend/data/ so the paths work regardless
# of which directory uvicorn/Python is launched from.
# formatter.py lives in backend/src/, so we go one level up to reach backend/data/.
DATA_DIR     = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
TEMPLATE_TEX = os.path.join(DATA_DIR, "template.tex")
OUTPUT_TEX   = os.path.join(DATA_DIR, "output.tex")
OUTPUT_PDF   = os.path.join(DATA_DIR, "output.pdf")


def generate_pdf(metadata, body_text):
    """
    Takes verified data, injects it into template.tex,
    and compiles it using the IEEEtran.cls stored in backend/data/.
    """
    try:
        # 1. Read the LaTeX skeleton from the fixed data directory
        with open(TEMPLATE_TEX, "r") as f:
            tex_content = f.read()

        # 2. Inject verified metadata
        tex_content = tex_content.replace("[[TITLE]]",    metadata.get('title', 'Untitled'))
        tex_content = tex_content.replace("[[AUTHORS]]",  metadata.get('authors', 'Anonymous'))
        tex_content = tex_content.replace("[[ABSTRACT]]", metadata.get('abstract', ''))
        tex_content = tex_content.replace("[[BODY]]",     body_text)

        # 3. Write the populated .tex to the data directory
        with open(OUTPUT_TEX, "w") as f:
            f.write(tex_content)

        # 4. Run pdflatex with cwd=DATA_DIR so that IEEEtran.cls (which lives
        #    in the same data/ folder) is found automatically by the LaTeX engine.
        subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", OUTPUT_TEX],
            cwd=DATA_DIR,
            check=True,
            capture_output=True,
        )

        # 5. Return the compiled PDF bytes
        if os.path.exists(OUTPUT_PDF):
            with open(OUTPUT_PDF, "rb") as f:
                return f.read()
        return None

    except Exception as e:
        return f"Formatting Error: {str(e)}".encode()
