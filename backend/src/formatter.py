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


def generate_pdf(metadata, body_text):
    """
    Injects metadata into template.tex (escaping LaTeX special chars and
    converting heading markers), then compiles with pdflatex.
    Returns raw PDF bytes on success, or raises RuntimeError on failure.
    """
    try:
        with open(TEMPLATE_TEX, "r", encoding="utf-8") as f:
            tex_content = f.read()

        # Escape metadata fields, convert body headings to LaTeX sections
        tex_content = tex_content.replace("[[TITLE]]",    _latex_escape(metadata.get('title',    'Untitled')))
        tex_content = tex_content.replace("[[AUTHORS]]",  _latex_escape(metadata.get('authors',  'Anonymous')))
        tex_content = tex_content.replace("[[ABSTRACT]]", _latex_escape(metadata.get('abstract', '')))
        # Tag known section headings using LLM-extracted list, filtered against title/authors
        headings_str = metadata.get('headings', '')
        tagged_body  = _apply_metadata_headings(body_text, headings_str, metadata)

        # ── Strip Preamble ──────────────────────────────────────────────
        # Find the first real section marker. The naive way (find the first @@H1@@)
        # fails if a DOCX style spuriously tagged the title or author line as a heading.
        # Instead, we look for 'Introduction' or the first LLM-extracted heading.
        cut_index = -1
        intro_match = re.search(r'@@H[123]@@(I\.?\s*)?Introduction@@END@@', tagged_body, re.IGNORECASE)
        if intro_match:
            cut_index = intro_match.start()
        else:
            # Fallback: cut at the first marker that comes AFTER the abstract text
            # (to avoid cutting at a spurious title marker)
            abstract_text = metadata.get('abstract', '').strip()
            if abstract_text and abstract_text in tagged_body:
                after_abs = tagged_body.find(abstract_text) + len(abstract_text)
                first_marker = tagged_body.find('@@H', after_abs)
                if first_marker != -1:
                    cut_index = first_marker
            else:
                # Last resort: just cut at the first marker
                cut_index = tagged_body.find('@@H')

        if cut_index > 0:
            tagged_body = tagged_body[cut_index:]

        # Finally, strip any hardcoded Roman numerals from the tagged headings
        # because \section{} generates its own Roman numerals.
        # Matches @@H1@@ I. Introduction @@END@@  ->  @@H1@@ Introduction @@END@@
        tagged_body = re.sub(
            r'(@@H[123]@@)\s*(?:[IVXLCDM]+\.|[0-9]+\.)\s*(.*?)(@@END@@)',
            r'\1\2\3',
            tagged_body,
            flags=re.IGNORECASE
        )

        tex_content = tex_content.replace("[[BODY]]", _convert_headings(tagged_body))

        with open(OUTPUT_TEX, "w", encoding="utf-8") as f:
            f.write(tex_content)

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

    except RuntimeError:
        raise
    except Exception as e:
        raise RuntimeError(f"Formatter Error: {e}") from e
