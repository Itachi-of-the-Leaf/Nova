import os
import subprocess

def generate_pdf(metadata, body_text):
    """
    Takes verified data, injects it into template.tex, 
    and compiles it using the IEEEtran.cls you just uploaded.
    """
    try:
        # 1. Read your LaTeX skeleton
        with open("template.tex", "r") as f:
            tex_content = f.read()

        # 2. Inject verified metadata from the "Glass Box" sidebar
        tex_content = tex_content.replace("[[TITLE]]", metadata.get('title', 'Untitled'))
        tex_content = tex_content.replace("[[AUTHORS]]", metadata.get('authors', 'Anonymous'))
        tex_content = tex_content.replace("[[ABSTRACT]]", metadata.get('abstract', ''))
        tex_content = tex_content.replace("[[BODY]]", body_text)

        # 3. Write to a temporary file for compilation
        with open("output.tex", "w") as f:
            f.write(tex_content)

        # 4. Run the headless LaTeX engine (must be installed in WSL)
        # nonstopmode ensures it doesn't freeze on minor LaTeX warnings
        subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", "output.tex"], 
            check=True, capture_output=True
        )

        # 5. Return the binary PDF data to Streamlit
        if os.path.exists("output.pdf"):
            with open("output.pdf", "rb") as f:
                return f.read()
        return None

    except Exception as e:
        return f"Formatting Error: {str(e)}".encode()
    
    