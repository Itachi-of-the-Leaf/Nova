import pytest
from unittest.mock import patch

@patch('unstructured.partition.auto.partition')
def test_fix_student_identifier_regex(mock_partition):
    from src.engine import extract_text_from_docx
    class DummyElement:
        def __init__(self, text):
            self.text = text
        def __str__(self):
            return self.text
    
    # Simulate unstructured extracting a corrupted identifier
    mock_partition.return_value = [
        DummyElement("Student $10 said they were studying English."),
        DummyElement("And $19 agreed with $16.")
    ]
    
    extracted = extract_text_from_docx("dummy.pdf")
    
    assert "Student S10 said" in extracted
    assert "And S19 agreed with S16" in extracted
    assert "$10" not in extracted
    assert "$19" not in extracted
