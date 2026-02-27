import pytest
from unittest.mock import patch
from src.engine import extract_text_from_docx

@patch('unstructured.partition.auto.partition')
def test_table_extraction_strategy_configured(mock_partition):
    # Mock unstructured to return a dummy element
    class DummyElement:
        def __str__(self): return "Dummy"
        metadata = type('obj', (object,), {'category_depth': 0})
    mock_partition.return_value = [DummyElement()]
    
    extract_text_from_docx("dummy.pdf")
    
    # Assert that the correct table extraction strategies were passed
    mock_partition.assert_called_with(
        filename="dummy.pdf",
        strategy="hi_res",
        hi_res_model_name="yolox",
        infer_table_structure=True,
        pdf_infer_table_structure=True
    )
