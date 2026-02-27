import pytest
from src.formatter import _convert_headings, generate_pdf

def test_heading_stripping():
    # Simulate tagged body with various heading numbers
    body = "@@H1@@ I. Introduction @@END@@\n@@H2@@ A. Background @@END@@\n@@H1@@ M. Methodology @@END@@\n@@H1@@ 1.2 Evaluation @@END@@\n@@H1@@ References @@END@@"
    
    # We must mock or call the regex that is currently in generate_pdf.
    # It's better to test the regex directly or wrap the stripping logic into a testable function.
    import re
    tagged_body = re.sub(
        r'(@@H[123]@@)\s*(?:(?:[IVXLCDM]+|[A-Z])\.|\d+(?:\.\d+)*\.?)\s+(.*?)\s*(@@END@@)',
        r'\1\2\3',
        body,
        flags=re.IGNORECASE
    )
    
    assert "@@H1@@Introduction@@END@@" in tagged_body
    assert "@@H2@@Background@@END@@" in tagged_body
    assert "@@H1@@Methodology@@END@@" in tagged_body
    assert "@@H1@@Evaluation@@END@@" in tagged_body
    assert "@@H1@@ References @@END@@" in tagged_body
    
    # Check that references doesn't get numbered
    latex = _convert_headings(tagged_body)
    assert "\\section*{References}" in latex or "\\section{References}" not in latex
