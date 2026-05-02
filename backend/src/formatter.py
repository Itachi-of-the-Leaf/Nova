import os
import re
import subprocess

DATA_DIR     = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
TEMPLATE_TEX = os.path.join(DATA_DIR, "template.tex")
OUTPUT_TEX   = os.path.join(DATA_DIR, "output.tex")
OUTPUT_PDF   = os.path.join(DATA_DIR, "output.pdf")
OUTPUT_LOG   = os.path.join(DATA_DIR, "output.log")


def _latex_escape(text: str) -> str:
    """Escape characters that have special meaning in LaTeX."""
    replacements = [
        ('\\', r'\textbackslash{}'),   # must be first
        ('&',  r'\&'),
        ('%',  r'\%'),
        ('$',  r'\$'),
        ('#',  r'\#'),
        ('_',  r'\_'),
        ('{',  r'\{'),
        ('}',  r'\}'),
        ('~',  r'\textasciitilde{}'),
        ('^',  r'\textasciicircum{}'),
    ]
    for char, escaped in replacements:
        text = text.replace(char, escaped)
    return text


def _convert_headings(text: str) -> str:
    """
    Convert @@H1@@...@@END@@ markers into LaTeX section commands.
    Plain text lines are LaTeX-escaped as-is.
    """
    lines = text.split('\n')
    latex_lines = []
    for line in lines:
        m1 = re.match(r'@@H1@@(.+?)@@END@@', line)
        m2 = re.match(r'@@H2@@(.+?)@@END@@', line)
        m3 = re.match(r'@@H3@@(.+?)@@END@@', line)
        if m1:
            latex_lines.append(f'\n\\section{{{_latex_escape(m1.group(1))}}}\n')
        elif m2:
            latex_lines.append(f'\n\\subsection{{{_latex_escape(m2.group(1))}}}\n')
        elif m3:
            latex_lines.append(f'\n\\subsubsection{{{_latex_escape(m3.group(1))}}}\n')
        else:
            latex_lines.append(_latex_escape(line))
            
    # Use double-newlines so LaTeX recognizes paragraph breaks instead of 
    # merging everything into single blocks. This also ensures each reference 
    # appears on a new line (if they were separate paragraphs in the original doc).
    return '\n\n'.join(latex_lines)


def _apply_metadata_headings(body_text: str, headings_str: str, metadata: dict) -> str:
    """
    Filters the @@H*@@ markers already placed by engine.extract_text_from_docx.
    Removes markers for lines that match the title, authors, or 'abstract' —
    those are already rendered by the LaTeX template header.

    As a fallback, also tags any LLM-extracted headings that weren't caught
    by DOCX styles (for documents with poor/missing heading styles).
    """
    title   = (metadata.get('title',   '') or '').lower().strip()
    authors = (metadata.get('authors', '') or '').lower().strip()
    SKIP_WORDS = {'abstract'}

    def _should_skip(text: str) -> bool:
        t = text.lower().strip()
        if t in SKIP_WORDS:                      return True
        if title   and (t in title   or title   in t): return True
        if authors and (t in authors or authors in t): return True
        if len(t) > 150:                         return True
        return False

    # ── Pass 1: strip markers from preamble/title/abstract lines ──────────
    def _clean_marker(m):
        inner = m.group(1)          # text inside the marker
        return inner if _should_skip(inner) else m.group(0)

    body_text = re.sub(r'@@H[123]@@(.+?)@@END@@', _clean_marker, body_text)

    # ── Pass 2: tag any LLM-extracted headings not already marked ─────────
    # (fallback for documents that don't use Word heading styles)
    if headings_str:
        raw_headings = re.split(r'[\n,;]+', headings_str)
        for heading in (h.strip() for h in raw_headings if h.strip()):
            if _should_skip(heading):
                continue
            # Only add a marker if the line has no marker yet
            pattern = rf'^(?!@@H)({re.escape(heading)})$'
            
            # If the LLM found 'References', keep it as a main section.
            # Otherwise, assume unstyled LLM headings are subsections (H2).
            # This fixes the issue where unstyled subsections (e.g. "Autonomy...") 
            # appear as back-to-back main sections right after the parent H1.
            repl_marker = r'@@H1@@\1@@END@@' if heading.lower() == 'references' else r'@@H2@@\1@@END@@'
            
            body_text = re.sub(
                pattern,
                repl_marker,
                body_text,
                count=1,
                flags=re.MULTILINE | re.IGNORECASE
            )

    return body_text


TEMP_DOCX    = os.path.join(DATA_DIR, "temp.docx")

def _fix_longtable(body: str) -> str:
    # A stateful parser to convert longtable to table + tabular
    def replacer(match):
        content = match.group(0)
        # Extract column spec
        colspec_match = re.search(r'\\begin\{longtable\}\[.*?\](\{.*?\})', content)
        if not colspec_match:
            colspec_match = re.search(r'\\begin\{longtable\}(\{.*?\})', content)
        colspec = colspec_match.group(1) if colspec_match else "{l}"
        
        # We will determine is_wide and table_env based on inner content count instead
        
        # Extract caption
        caption = ""
        caption_match = re.search(r'(\\caption\{.*?\})', content, re.DOTALL)
        if caption_match:
            caption = caption_match.group(1)
            # Remove caption from content
            content = content.replace(caption_match.group(0), "")
            
        # Strip longtable headers and footers
        content = re.sub(r'\\endfirsthead', '', content)
        content = re.sub(r'\\endhead', '', content)
        content = re.sub(r'\\endfoot', '', content)
        content = re.sub(r'\\endlastfoot', '', content)
        
        # Get just the inner rows by stripping begin and end tags
        inner_content = re.sub(r'\\begin\{longtable\}(\[.*?\])?\{.*?\}', '', content)
        inner_content = re.sub(r'\\end\{longtable\}', '', inner_content)
        
        # Dynamically count columns using the first data row's & delimiters
        first_row_match = re.search(r'^.*?&.*?\\\\', inner_content, re.MULTILINE)
        if first_row_match:
            num_cols = first_row_match.group(0).count('&') + 1
        else:
            num_cols = 1
            
        # Determine if table is wide
        is_wide = num_cols > 2
        table_env = "table*" if is_wide else "table"
        
        # Create a clean tabularx column spec, forcing equal widths that span the page
        simple_colspec = "{" + ("X" * num_cols) + "}"
        width_arg = r"{\textwidth}" if is_wide else r"{\columnwidth}"
        
        # Reconstruct using tabularx to perfectly balance text wrapping across the full width
        res = f"\\begin{{{table_env}}}[htbp]\n\\centering\n"
        if caption:
            res += f"{caption}\n"
        res += f"\\begin{{tabularx}}{width_arg}{simple_colspec}\n"
        res += inner_content.strip() + "\n"
        res += f"\\end{{tabularx}}\n\\end{{{table_env}}}"
        return res

    return re.sub(r'\\begin\{longtable\}.*?\\end\{longtable\}', replacer, body, flags=re.DOTALL)


def _fix_figure_envs(body: str) -> str:
    # Ensure figures have [htbp] and \centering
    def replacer(match):
        inner = match.group(1)
        # Extract caption if any
        caption_match = re.search(r'\\caption\{.*?\}', inner, re.DOTALL)
        caption = caption_match.group(0) if caption_match else ""
        if caption:
            inner = inner.replace(caption, "")
            
        # Make sure graphics are centered
        if r'\centering' not in inner:
            inner = r'\centering' + '\n' + inner.strip()
            
        # Reconstruct with caption below
        res = "\\begin{figure}[htbp]\n"
        res += inner.strip() + "\n"
        if caption:
            res += f"{caption}\n"
        res += "\\end{figure}"
        return res
        
    body = re.sub(r'\\begin\{figure\}(?:\[.*?\])?(.*?)\\end\{figure\}', replacer, body, flags=re.DOTALL)
    
    # Also wrap bare includegraphics not inside a figure
    def bare_replacer(match):
        # We can't easily know if it's inside a figure with regex, 
        # but since we just normalized all figures, we can do a negative lookbehind/lookahead if we were careful.
        # A simpler way is to just let Pandoc handle it, as Pandoc usually wraps images in figures if they are paragraphs.
        # For inline images, wrapping them in float breaks the text. So let's skip wrapping bare graphics for now.
        return match.group(0)
        
    return body


def _strip_preamble(body: str, metadata: dict) -> str:
    strategies = [
        r'\\section\*?\{',
        r'\\subsection\*?\{',
        r'\\section\*?\{[IVX]+\.',
    ]
    
    # First try to find abstract end if Pandoc generated one
    abstract_end_match = re.search(r'\\end\{abstract\}', body)
    if abstract_end_match:
         return body[abstract_end_match.end():].strip()
         
    # Else try section headings
    for pattern in strategies:
        m = re.search(pattern, body)
        if m:
            return body[m.start():].strip()
            
    # Fallback, just return as is
    return body


def generate_pdf(metadata, body_text):
    """
    Converts TEMP_DOCX to LaTeX using Pandoc to preserve images, tables, and equations.
    Strips the original preamble (Title/Authors/Abstract) and injects the cleaned body
    into template.tex with AI-verified metadata.
    """
    try:
        # Step 1: Run Pandoc on the original DOCX to generate a LaTeX body
        pandoc_out = os.path.join(DATA_DIR, "body_pandoc.tex")
        media_dir = os.path.join(DATA_DIR, "media")
        subprocess.run(
            ["pandoc", TEMP_DOCX, "-o", pandoc_out, f"--extract-media={media_dir}", "--wrap=none"],
            cwd=DATA_DIR,
            capture_output=True,
            check=True
        )

        with open(pandoc_out, "r", encoding="utf-8") as f:
            pandoc_body = f.read()

        # Fix image paths to be absolute
        # Pandoc writes \includegraphics{media/image1.png} or similar.
        # We need absolute paths for pdflatex.
        def path_replacer(m):
            opt = m.group(1) or ""
            rel_path = m.group(2)
            abs_path = os.path.join(DATA_DIR, rel_path).replace("\\", "/")
            return f"\\pandocbounded{{\\includegraphics{opt}{{{abs_path}}}}}"
            
        pandoc_body = re.sub(r'\\includegraphics(\[.*?\])?\{((?:media[/\\])?[^}]+)\}', path_replacer, pandoc_body)

        # Fix longtable for IEEE 2-column compatibility
        pandoc_body = _fix_longtable(pandoc_body)
        
        # Fix figure environments
        pandoc_body = _fix_figure_envs(pandoc_body)

        # Step 2: Strip Preamble (Title, Authors, Abstract) to prevent duplication
        pandoc_body = _strip_preamble(pandoc_body, metadata)

        # Step 3: Read and populate template.tex
        with open(TEMPLATE_TEX, "r", encoding="utf-8") as f:
            tex_content = f.read()

        tex_content = tex_content.replace("[[TITLE]]",    _latex_escape(metadata.get('title',    'Untitled')))
        tex_content = tex_content.replace("[[AUTHORS]]",  _latex_escape(metadata.get('authors',  'Anonymous')))
        tex_content = tex_content.replace("[[ABSTRACT]]", _latex_escape(metadata.get('abstract', '')))
        
        # Ensure we do NOT escape pandoc_body, as it is already valid LaTeX
        tex_content = tex_content.replace("[[BODY]]", pandoc_body)

        with open(OUTPUT_TEX, "w", encoding="utf-8") as f:
            f.write(tex_content)

        # Step 4: Compile the PDF
        result = subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", OUTPUT_TEX],
            cwd=DATA_DIR,
            capture_output=True,
        )

        if result.returncode != 0:
            log = ""
            if os.path.exists(OUTPUT_LOG):
                with open(OUTPUT_LOG, "r", encoding="utf-8", errors="replace") as f:
                    log = f.read()
            error_line = next(
                (line for line in log.splitlines() if line.startswith("!")),
                result.stderr.decode(errors="replace") or "Unknown LaTeX error"
            )
            raise RuntimeError(f"LaTeX compile error: {error_line}")

        if os.path.exists(OUTPUT_PDF):
            with open(OUTPUT_PDF, "rb") as f:
                return f.read()

        raise RuntimeError("pdflatex ran but produced no output.pdf")

    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Pandoc Error: {e.stderr.decode(errors='replace')}") from e
    except RuntimeError:
        raise
    except Exception as e:
        raise RuntimeError(f"Formatter Error: {e}") from e
