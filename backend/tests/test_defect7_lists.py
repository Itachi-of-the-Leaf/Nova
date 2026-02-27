import pytest
import re
from src.formatter import _convert_headings

def test_defect7_list_items():
    # Simulate a tagged list sequence
    body = "Here is a list:\n@@LIST_ITEM@@ First item @@END@@\n@@LIST_ITEM@@ Second item @@END@@\nNext paragraph."
    
    latex = _convert_headings(body)
    
    # Assert proper itemize wrapping
    assert "\\begin{itemize}" in latex
    assert "\\item First item" in latex
    assert "\\item Second item" in latex
    assert "\\end{itemize}" in latex
    
    # Ensure they are contiguous within the block
    assert latex.find("\\begin{itemize}") < latex.find("\\item First item")
    assert latex.find("\\item Second item") < latex.find("\\end{itemize}")
