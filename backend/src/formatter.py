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
    Intercepts [TABLE_START]...[TABLE_END] to transpile nested HTML to LaTeX tabular.
    Plain text lines are LaTeX-escaped as-is.
    """
    from bs4 import BeautifulSoup

    def _html_to_latex_table(html_str: str) -> str:
        soup = BeautifulSoup(html_str, 'html.parser')
        table = soup.find('table')
        if not table:
            return _latex_escape(html_str)
            
        rows = table.find_all('tr')
        if not rows:
            return ""
            
        # Determine max columns
        max_cols = max((len(r.find_all(['td', 'th'])) for r in rows), default=1)
        col_format = "l" * max_cols
        
        latex_str = "\\begin{table}[h!]\n\\centering\n\\begin{tabular}{" + col_format + "}\n\\hline\n"
        
        for row in rows:
            cells = row.find_all(['td', 'th'])
            # Clean and escape each cell's text
            escaped_cells = [_latex_escape(cell.get_text(strip=True)) for cell in cells]
            # Pad if row has fewer cells
            padded_cells = escaped_cells + [""] * (max_cols - len(escaped_cells))
            latex_str += " & ".join(padded_cells) + " \\\\\n"
            
        latex_str += "\\hline\n\\end{tabular}\n\\end{table}\n"
        return latex_str

    # Process block by block
    # We will split the text by table markers first
    blocks = re.split(r'(\[TABLE_START\][\s\S]*?\[TABLE_END\])', text)
    
    final_latex_parts = []
    
    for block in blocks:
        if block.startswith('[TABLE_START]') and block.endswith('[TABLE_END]'):
            html_content = block[13:-11].strip() # strip the markers
            final_latex_parts.append(_html_to_latex_table(html_content))
            continue
            
        # Standard line-by-line processing for headings and text
        lines = block.split('\n')
        in_list = False
        
        for line in lines:
            m1 = re.match(r'@@H1@@(.*?)@@END@@', line)
            m2 = re.match(r'@@H2@@(.*?)@@END@@', line)
            m3 = re.match(r'@@H3@@(.*?)@@END@@', line)
            m_list = re.match(r'@@LIST_ITEM@@(.*?)@@END@@', line)
            
            # Context-switching for LaTeX Itemize block
            if m_list and not in_list:
                final_latex_parts.append('\\begin{itemize}')
                in_list = True
            elif not m_list and in_list:
                final_latex_parts.append('\\end{itemize}')
                in_list = False
                
            if m_list:
                final_latex_parts.append(f'\\item {_latex_escape(m_list.group(1).strip())}')
            elif m1:
                heading_text = m1.group(1)
                if heading_text.lower().strip() == 'references':
                    final_latex_parts.append(f'\n\\section*{{{_latex_escape(heading_text)}}}\n')
                else:
                    final_latex_parts.append(f'\n\\section{{{_latex_escape(heading_text)}}}\n')
            elif m2:
                final_latex_parts.append(f'\n\\subsection{{{_latex_escape(m2.group(1))}}}\n')
            elif m3:
                final_latex_parts.append(f'\n\\subsubsection{{{_latex_escape(m3.group(1))}}}\n')
            else:
                if line.strip():
                    escaped_line = _latex_escape(line)
                    escaped_line = re.sub(r'@@FOOTNOTE@@(.*?)@@END@@', r'\\footnote{\1}', escaped_line)
                    final_latex_parts.append(escaped_line)
                else:
                    final_latex_parts.append("") # preserve double newline logic
                    
        # Conclude itemize context if block ended on list
        if in_list:
            final_latex_parts.append('\\end{itemize}')

    return '\n\n'.join(final_latex_parts)


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

        # Finally, strip any hardcoded Roman numerals, alphabetical, or decimal list indices 
        # from the tagged headings because \section{} generates its own numbering.
        tagged_body = re.sub(
            r'(@@H[123]@@)\s*(?:(?:[IVXLCDM]+|[A-Z])\.|\d+(?:\.\d+)*\.?)\s+(.*?)\s*(@@END@@)',
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
