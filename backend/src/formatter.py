import os
import re
import subprocess

DATA_DIR     = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
TEMPLATE_TEX = os.path.join(DATA_DIR, "template.tex")


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

def _extract_caption(text: str) -> tuple[str, str]:
    r"""Extracts the first \caption{...} or \caption[...]{...} from text, handling nested braces.
    Returns (caption_text, remaining_text)."""
    m = re.search(r'\\caption\s*(?:\[[^\]]*\])?\s*\{', text)
    if not m:
        return "", text
        
    idx = m.start()
    start_brace = m.end() - 1
    
    brace_count = 0
    end_idx = -1
    for i in range(start_brace, len(text)):
        if text[i] == '{':
            brace_count += 1
        elif text[i] == '}':
            brace_count -= 1
            if brace_count == 0:
                end_idx = i
                break
                
    if end_idx != -1:
        caption = text[idx:end_idx+1]
        remaining = text[:idx] + text[end_idx+1:]
        return caption, remaining

    return "", text


def _count_longtable_cols(longtable_text: str) -> int:
    """
    Extract the column count from the \begin{longtable}[opt]{colspec} column spec.
    This is far more reliable than counting & in rows, which breaks on multi-line
    minipage cells that Pandoc generates.
    """
    # Find \begin{longtable} and advance past optional [...]
    m = re.search(r'\\begin\{longtable\}', longtable_text)
    if not m:
        return 1
    curr = m.end()
    text = longtable_text
    # Skip optional [...]
    while curr < len(text) and text[curr].isspace(): curr += 1
    if curr < len(text) and text[curr] == '[':
        depth = 0
        while curr < len(text):
            if text[curr] == '[': depth += 1
            elif text[curr] == ']':
                depth -= 1
                if depth == 0: curr += 1; break
            curr += 1
    # Skip whitespace then read the mandatory {...} colspec
    while curr < len(text) and text[curr].isspace(): curr += 1
    colspec = ""
    if curr < len(text) and text[curr] == '{':
        depth = 0
        start = curr + 1
        while curr < len(text):
            if text[curr] == '{': depth += 1
            elif text[curr] == '}':
                depth -= 1
                if depth == 0:
                    colspec = text[start:curr]
                    break
            curr += 1
    if not colspec:
        return 1
    # Strip everything inside balanced braces to avoid counting formatting commands
    res = []
    depth = 0
    for char in colspec:
        if char == '{':
            depth += 1
        elif char == '}':
            depth -= 1
        else:
            if depth == 0:
                res.append(char)
    cleaned = "".join(res)
    col_letters = re.sub(r'[@!><|]', '', cleaned)
    col_letters = re.sub(r'[^lcrmbjXLRCJSpw]', '', col_letters)
    return max(len(col_letters), 1)


def _strip_minipage_wrappers(text: str) -> str:
    r"""
    Remove \begin{minipage}[...]{...} ... \end{minipage} wrappers and
    \begin{quote} ... \end{quote} wrappers that Pandoc inserts inside table
    cells. Keeps the inner content so table rows remain valid LaTeX.
    """
    # Strip minipage: \begin{minipage}[opt]{width} ... \end{minipage}
    text = re.sub(
        r'\\begin\{minipage\}(?:\[[^\]]*\])?\{[^}]*\}(.*?)\\end\{minipage\}',
        lambda m: m.group(1).strip(),
        text, flags=re.DOTALL
    )
    # Strip quote environments
    text = re.sub(
        r'\\begin\{quote\}(.*?)\\end\{quote\}',
        lambda m: m.group(1).strip(),
        text, flags=re.DOTALL
    )
    # Strip raggedright added by Pandoc which redefines \\ inside tabularx X columns
    text = text.replace(r'\raggedright', '')
    return text

def _fix_pseudo_tables(text: str) -> str:
    """
    Find quote environments containing pseudo-tables (e.g. Table 3) that Pandoc
    failed to recognize as tables, and convert them to tabularx.
    """
    def replacer(match):
        content = match.group(1)
        # Remove any stray phantomsection or label macros from the content
        content = re.sub(r'\\protect\\phantomsection\\label\{[^}]*\}\{\}', '', content)
        
        lines = [l.strip() for l in content.split('\n') if l.strip()]
        if len(lines) < 4: return match.group(0)
        
        m_title = re.search(r'\\textbf\{(Table\s+\d+)\}', lines[0])
        if not m_title: return match.group(0)
        table_label = m_title.group(1)
        
        caption = lines[1]
        headers = lines[2].split()
        num_cols = len(headers)
        if num_cols < 2: return match.group(0)
        
        colspec = '{|' + '|'.join(['X'] * num_cols) + '|}'
        # Use table* so it spans both columns
        res = f'\\begin{{table*}}[htbp]\n\\centering\n\\caption{{{table_label}: {caption}}}\n'
        res += f'\\begin{{tabularx}}{{\\textwidth}}{colspec}\n\\hline\n'
        res += ' & '.join(headers) + ' \\\\\n\\hline\n'
        
        for line in lines[3:]:
            if re.match(r'^\d+\.\s+', line):
                res += f'\\multicolumn{{{num_cols}}}{{|l|}}{{\\textbf{{{line}}}}} \\\\\n\\hline\n'
                continue
            if num_cols == 3:
                parts = line.rsplit(' ', 1)
                if len(parts) == 2 and parts[1].isdigit():
                    num = parts[1]
                    rest = parts[0]
                    words = rest.split(' ', 1)
                    if len(words) == 2 and words[0].istitle() and words[1] and words[1][0].istitle():
                        col1, col2 = words[0], words[1]
                    else:
                        col1, col2 = '', rest
                    res += f'{col1} & {col2} & {num} \\\\\n\\hline\n'
                else:
                    res += f'\\multicolumn{{{num_cols}}}{{|l|}}{{{line}}} \\\\\n\\hline\n'
            else:
                res += f'\\multicolumn{{{num_cols}}}{{|l|}}{{{line}}} \\\\\n\\hline\n'
        res += '\\end{tabularx}\n\\end{table*}\n'
        return res

    def wrapper(match):
        content = match.group(1)
        if r'\textbf{Table' not in content:
            return match.group(0)
        return replacer(match)

    return re.sub(r'\\begin\{quote\}(.*?)\\end\{quote\}', wrapper, text, flags=re.DOTALL)


def _fix_longtable(body: str) -> str:
    """Convert longtable environments to table/table* + tabularx with full grid lines."""
    def replacer(match):
        content = match.group(0)

        # ── Extract column count BEFORE stripping \begin{longtable} ──────────
        num_cols = _count_longtable_cols(content)

        # ── Extract caption ───────────────────────────────────────────────────
        caption, content = _extract_caption(content)

        # ── Strip \begin{longtable}[...]{...} ────────────────────────────────
        def strip_begin(text):
            idx = text.find(r'\begin{longtable}')
            if idx == -1: return text
            curr = idx + len(r'\begin{longtable}')
            while curr < len(text) and text[curr].isspace(): curr += 1
            if curr < len(text) and text[curr] == '[':
                d = 0
                while curr < len(text):
                    if text[curr] == '[': d += 1
                    elif text[curr] == ']':
                        d -= 1
                        if d == 0: curr += 1; break
                    curr += 1
            while curr < len(text) and text[curr].isspace(): curr += 1
            if curr < len(text) and text[curr] == '{':
                d = 0
                while curr < len(text):
                    if text[curr] == '{': d += 1
                    elif text[curr] == '}':
                        d -= 1
                        if d == 0: curr += 1; break
                    curr += 1
            return text[curr:]

        inner_content = strip_begin(content)
        inner_content = inner_content.replace(r'\end{longtable}', '')

        # ── Clean up header/footer blocks from Pandoc ────────────────────────
        # Remove redundant repeated headers and footers at the top of the longtable
        inner_content = re.sub(r'(?:\\endfirsthead|\\endhead).*?\\endlastfoot\n?', '', inner_content, flags=re.DOTALL)
        
        # Remove \noalign{} which causes "! Misplaced \noalign." errors in tabularx
        inner_content = inner_content.replace(r'\noalign{}', '')

        # ── Strip minipage/quote wrappers Pandoc adds inside cells ───────────
        inner_content = _strip_minipage_wrappers(inner_content)

        # ── Build tabularx environment with full grid lines ───────────────────
        is_wide   = num_cols > 2
        table_env = "table*" if is_wide else "table"
        colspec   = "{|" + "|".join(["X"] * num_cols) + "|}"
        width_arg = r"{\textwidth}" if is_wide else r"{\columnwidth}"

        inner_content = inner_content.strip()
        
        # Replace booktabs rules with \hline
        inner_content = inner_content.replace(r'\toprule', r'\hline')
        inner_content = inner_content.replace(r'\midrule', r'\hline')
        inner_content = inner_content.replace(r'\bottomrule', r'\hline')
        
        # Add \hline between rows (after every \\ that doesn't already have \hline)
        inner_content = re.sub(r'\\\\(?!\s*\\hline)', r'\\\\ \n\\hline', inner_content)

        res  = f"\\begin{{{table_env}}}[htbp]\n\\centering\n"
        if caption:
            res += f"{caption}\n"
        res += f"\\begin{{tabularx}}{width_arg}{colspec}\n"
        res += inner_content.strip() + "\n"
        res += f"\\end{{tabularx}}\n\\end{{{table_env}}}"
        return res

    return re.sub(r'\\begin\{longtable\}.*?\\end\{longtable\}', replacer, body, flags=re.DOTALL)


def _fix_figure_envs(body: str) -> str:
    # Ensure figures have [htbp] and \centering
    def replacer(match):
        inner = match.group(1)
        # Extract caption if any
        caption, inner = _extract_caption(inner)
            
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
    
    # Wrap bare includegraphics not inside a figure, bundling them with their captions
    paragraphs = body.split('\n\n')
    new_paragraphs = []
    i = 0
    while i < len(paragraphs):
        p = paragraphs[i]
        if r'\includegraphics' in p and r'\begin{figure}' not in p:
            caption_p = None
            merge_count = 0
            
            if r'\textbf{Fig.' in p:
                caption_p = p
                merge_count = 0
            else:
                if i + 1 < len(paragraphs) and r'\textbf{Fig.' in paragraphs[i+1]:
                    caption_p = paragraphs[i+1]
                    merge_count = 1
                elif i + 2 < len(paragraphs) and r'\textbf{Fig.' in paragraphs[i+2] and r'\includegraphics' not in paragraphs[i+1]:
                    caption_p = paragraphs[i+1] + '\n\n' + paragraphs[i+2]
                    merge_count = 2
                    
            if caption_p is not None:
                if merge_count == 0:
                    combined = p
                else:
                    combined = p + '\n\n' + caption_p
                res = f'\\begin{{figure}}[htbp]\n\\centering\n{combined}\n\\end{{figure}}'
                new_paragraphs.append(res)
                i += 1 + merge_count
                continue
                
            res = f'\\begin{{figure}}[htbp]\n\\centering\n{p}\n\\end{{figure}}'
            new_paragraphs.append(res)
            i += 1
        else:
            new_paragraphs.append(p)
            i += 1
            
    return '\n\n'.join(new_paragraphs)


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


def _linkify_citations(body: str, ref_list: list) -> str:
    """
    Post-process Pandoc LaTeX body to standardize and link citations.
    1. Replaces APA-style citations (Wang, 2014) in the text with IEEE [N].
    2. Links [N] markers to the references section via \\hyperref.
    3. Rebuilds the References section entirely using the verified ref_list
       so that it is perfectly numbered and formatted.
    """
    if not ref_list:
        # Fallback if no structured references are available
        return body

    # ── Split at the References section boundary ─────────────────────────────
    ref_section_re = re.compile(
        r'(\\(?:section|subsection)\*?\s*\{[^}]*[Rr]eferences[^}]*\})',
        re.DOTALL
    )
    ref_match = ref_section_re.search(body)

    if ref_match:
        pre_refs   = body[:ref_match.start()]
        ref_header = ref_match.group(1)
    else:
        pre_refs   = body
        ref_header = "\\section*{References}"

    # ── 1. Standardize APA Citations in Body Text ────────────────────────────
    # Build a map of "LastName_Year" -> Number
    ref_map = {}
    for ref in ref_list:
        m_year = re.search(r'\b(19|20)\d{2}\b', ref['text'])
        if not m_year: continue
        year = m_year.group(0)
        
        first_word = re.split(r'[,.]', ref['text'])[0].strip()
        last_name = first_word.split()[-1] if first_word else ""
        if last_name:
            ref_map[f"{last_name}_{year}"] = ref['number']

    def apa_replacer(match):
        citation_text = match.group(0)
        years = re.findall(r'\b(19|20)\d{2}\b', citation_text)
        if not years: return citation_text
        
        numbers = []
        for key, num in ref_map.items():
            author, year = key.split('_')
            # Check if author name AND year exist in this citation block
            if author.lower() in citation_text.lower() and year in citation_text:
                numbers.append(num)
                
        if numbers:
            numbers = sorted(list(set(numbers)))
            if len(numbers) == 1: return f"[{numbers[0]}]"
            else: return "[" + ", ".join(str(n) for n in numbers) + "]"
        return citation_text

    # Replace (Author, Year) or Author et al. (Year)
    pre_refs = re.sub(r'\([A-Za-z][^\)]*?(19|20)\d{2}[^\)]*?\)', apa_replacer, pre_refs)
    pre_refs = re.sub(r'[A-Z][a-z]+(?:\s+et\s+al\.)?\s*\((19|20)\d{2}\)', apa_replacer, pre_refs)

    # ── 2. Linkify [N] in body text ──────────────────────────────────────────
    def _make_link(m):
        n = m.group(1)
        return f'\\hyperref[ref:{n}]{{[{n}]}}'

    # Standard [N] form
    linked = re.sub(r'\[(\d{1,4})\]', _make_link, pre_refs)
    # Pandoc sometimes escapes brackets as {[}N{]}
    linked = re.sub(
        r'\{\\?\[\}(\d{1,4})\{\\?\]\}',
        lambda m: f'\\hyperref[ref:{m.group(1)}]{{[{m.group(1)}]}}',
        linked
    )

    # ── 3. Rebuild References Section ────────────────────────────────────────
    # Completely rebuild references from the verified ref_list.
    rebuilt_refs = [ref_header + "\n\n\\begin{itemize}"]
    for ref in ref_list:
        n = ref['number']
        # Clean up any existing [N] or N. at the start of the text
        clean_text = re.sub(r'^\[?\d+\]?[.)]?\s*', '', ref['text']).strip()
        
        # Escape LaTeX special chars using a quick local inline function
        # since _latex_escape might not be globally available here
        replacements = [('\\', r'\textbackslash{}'), ('&', r'\&'), ('%', r'\%'), ('$', r'\$'), ('#', r'\#'), ('_', r'\_'), ('{', r'\{'), ('}', r'\}'), ('~', r'\textasciitilde{}'), ('^', r'\textasciicircum{}')]
        for char, escaped in replacements:
            clean_text = clean_text.replace(char, escaped)
            
        item = f"\\item[\\label{{ref:{n}}}[{n}]] {clean_text}"
        rebuilt_refs.append(item)
    rebuilt_refs.append("\\end{itemize}")

    return linked + "\n".join(rebuilt_refs)
def _long_path(p: str) -> str:
    """Resolve Windows 8.3 short paths (e.g. ANIKET~1) to their full long form.

    pdflatex treats '~' as a LaTeX non-breaking space, so short paths like
    C:/Users/ANIKET~1/... cause "I can't find file" fatal errors.
    On non-Windows systems this is a no-op.
    """
    if os.name != 'nt':
        return p

    try:
        import ctypes
        buf = ctypes.create_unicode_buffer(512)
        ctypes.windll.kernel32.GetLongPathNameW(p, buf, 512)
        return buf.value or p
    except Exception:
        return p


def generate_pdf(metadata, body_text):
    """
    Converts TEMP_DOCX to LaTeX using Pandoc to preserve images, tables, and equations.
    Strips the original preamble (Title/Authors/Abstract) and injects the cleaned body
    into template.tex with AI-verified metadata.

    All intermediate/output files are written to a system temp directory so that
    uvicorn's --reload file-watcher does NOT restart the server mid-request.
    """
    import tempfile
    import shutil

    # Resolve to long path — Windows 8.3 short names contain '~' which is
    # a special character in LaTeX and makes pdflatex unable to find files.
    work_dir = _long_path(tempfile.mkdtemp(prefix="nova_pdf_"))
    try:
        # Step 1: Run Pandoc on the original DOCX to generate a LaTeX body
        pandoc_out = os.path.join(work_dir, "body_pandoc.tex")
        media_dir = os.path.join(work_dir, "media")
        subprocess.run(
            ["pandoc", TEMP_DOCX, "-o", pandoc_out, f"--extract-media={media_dir}", "--wrap=none"],
            cwd=work_dir,
            capture_output=True,
            check=True
        )

        with open(pandoc_out, "r", encoding="utf-8") as f:
            pandoc_body = f.read()

        # Fix image paths to be absolute (pointing into the temp media dir)
        # Use _long_path to ensure no '~' in embedded LaTeX paths
        def path_replacer(m):
            opt = m.group(1) or ""
            rel_path = m.group(2)
            abs_path = _long_path(os.path.join(work_dir, rel_path)).replace("\\", "/")
            return f"\\pandocbounded{{\\includegraphics{opt}{{{abs_path}}}}}"
            
        pandoc_body = re.sub(r'\\includegraphics(\[.*?\])?\{((?:media[/\\])?[^}]+)\}', path_replacer, pandoc_body)

        # Fix longtable for IEEE 2-column compatibility
        pandoc_body = _fix_longtable(pandoc_body)
        
        # Fix pseudo-tables (like Table 3) that Pandoc extracted as text blockquotes
        # Run this AFTER _fix_longtable so we don't accidentally match \begin{quote} blocks
        # that Pandoc puts inside longtable cells (which _fix_longtable strips out).
        pandoc_body = _fix_pseudo_tables(pandoc_body)
        
        # Fix figure environments
        pandoc_body = _fix_figure_envs(pandoc_body)

        # Step 2: Strip Preamble (Title, Authors, Abstract) to prevent duplication
        pandoc_body = _strip_preamble(pandoc_body, metadata)

        # Step 2b: Standardize APA citations to IEEE [N], link them, and rebuild the References section
        pandoc_body = _linkify_citations(pandoc_body, metadata.get('references_list', []))


        with open(TEMPLATE_TEX, "r", encoding="utf-8") as f:
            tex_content = f.read()

        def _format_authors(authors_str):
            if not authors_str or authors_str == 'Anonymous':
                return '\\IEEEauthorblockN{Anonymous}'
            # Split by comma or 'and'
            parts = re.split(r',\s*(?:and\s+)?|\s+and\s+', authors_str)
            names = [p.strip() for p in parts if p.strip()]
            if not names:
                return '\\IEEEauthorblockN{Anonymous}'
            
            blocks = []
            for name in names:
                blocks.append(f'\\IEEEauthorblockN{{{_latex_escape(name)}}}')
                
            return ' \\and\n'.join(blocks)

        tex_content = tex_content.replace("[[TITLE]]",    _latex_escape(metadata.get('title',    'Untitled')))
        tex_content = tex_content.replace("[[AUTHORS]]",  _format_authors(metadata.get('authors', 'Anonymous')))
        tex_content = tex_content.replace("[[ABSTRACT]]", _latex_escape(metadata.get('abstract', '')))
        
        # Ensure we do NOT escape pandoc_body, as it is already valid LaTeX
        tex_content = tex_content.replace("[[BODY]]", pandoc_body)

        output_tex = os.path.join(work_dir, "output.tex")
        with open(output_tex, "w", encoding="utf-8") as f:
            f.write(tex_content)

        # Copy IEEEtran.cls into the work dir so pdflatex can find it
        cls_src = os.path.join(DATA_DIR, "IEEEtran.cls")
        if os.path.exists(cls_src):
            shutil.copy2(cls_src, work_dir)

        # Step 4: Compile the PDF
        # Pass just the filename so pdflatex doesn't see any '~' in the path.
        # The cwd is already set to work_dir.
        result = subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", "output.tex"],
            cwd=work_dir,
            capture_output=True,
        )

        output_pdf = os.path.join(work_dir, "output.pdf")
        output_log = os.path.join(work_dir, "output.log")
        texput_log = os.path.join(work_dir, "texput.log")

        # Check for the PDF FIRST — MiKTeX often returns non-zero exit codes
        # for harmless warnings (e.g. "you have not checked for MiKTeX updates")
        # even when the PDF was generated successfully.
        if os.path.exists(output_pdf) and os.path.getsize(output_pdf) > 0:
            with open(output_pdf, "rb") as f:
                return f.read()

        # PDF is missing — now extract the real error from the log
        if result.returncode != 0:
            log = ""
            # pdflatex writes to output.log normally, but falls back to
            # texput.log if it can't even open the input file.
            log_path = output_log if os.path.exists(output_log) else texput_log
            if os.path.exists(log_path):
                with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                    log = f.read()
            error_line = next(
                (line for line in log.splitlines() if line.startswith("!")),
                result.stderr.decode(errors="replace") or "Unknown LaTeX error"
            )
            raise RuntimeError(f"LaTeX compile error: {error_line}")

        raise RuntimeError("pdflatex ran but produced no output.pdf")

    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Pandoc Error: {e.stderr.decode(errors='replace')}") from e
    except RuntimeError:
        raise
    except Exception as e:
        raise RuntimeError(f"Formatter Error: {e}") from e
    finally:
        # Clean up the temp directory — never leave stale files
        shutil.rmtree(work_dir, ignore_errors=True)
