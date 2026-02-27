import sys
sys.path.append("backend")

from src.formatter import generate_pdf
import re

body = """
Some text
[TABLE_START]
<table><tr><td>DATA</td></tr></table>
[TABLE_END]
@@H1@@Introduction@@END@@
More text.
"""
metadata = {"title": "T", "authors": "A", "abstract": "B", "headings": "Introduction"}

tex = generate_pdf(metadata, body)
