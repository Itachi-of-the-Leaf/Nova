import pytest
from src.formatter import _convert_headings

def test_html_table_to_latex():
    body_text = """Some text before table.
[TABLE_START]
<table>
<thead><tr><th>Header 1</th><th>Header 2</th></tr></thead>
<tbody>
<tr><td>Cell 1</td><td>Cell 2</td></tr>
<tr><td>Cell 3</td><td>Cell 4</td></tr>
</tbody>
</table>
[TABLE_END]
Some text after table."""

    result = _convert_headings(body_text)
    
    assert "\\begin{table*" in result or "\\begin{table" in result
    assert "\\begin{tabular}" in result
    assert "Header 1 & Header 2" in result
    assert "Cell 1 & Cell 2" in result
    assert "Cell 3 & Cell 4" in result
    assert "\\end{tabular}" in result
    assert "Some text before table." in result
    assert "Some text after table." in result
