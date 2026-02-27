import pytest
from unittest.mock import patch
from src.engine import extract_text_from_docx

@patch('unstructured.partition.auto.partition')
def test_data_truncation_chunking_strategy(mock_partition):
    class DummyElement:
        def __init__(self, text):
            self.text = text
        def __str__(self): return self.text
        metadata = type('obj', (object,), {'category_depth': 0})

    mock_partition.return_value = [DummyElement("Chunking test.")]
    
    extract_text_from_docx("dummy.pdf")
    
    # Assert unstructured was called with chunking_strategy="by_title" to group severed paragraphs
    mock_partition.assert_called_with(
        filename="dummy.pdf",
        strategy="hi_res",
        hi_res_model_name="yolox",
        infer_table_structure=True,
        pdf_infer_table_structure=True,
        chunking_strategy="by_title"
    )
