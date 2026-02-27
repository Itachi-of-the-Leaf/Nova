import pytest
from unittest.mock import patch, MagicMock
from src.verifier import verify_single_citation

@patch('src.verifier.urllib.request.urlopen')
def test_defect5_hallucinated_dates(mock_urlopen):
    # Mock Crossref returning an impossible year 2069
    mock_response = MagicMock()
    mock_response.read.return_value = b'{"message": {"items": [{"score": 80, "title": ["Test Paper"], "author": [{"family": "Smith", "given": "John"}], "issued": {"date-parts": [[2069]]}}]}}'
    mock_urlopen.return_value.__enter__.return_value = mock_response

    original_citation = "Smith, J. (1996). Test Paper. Journal of Testing."
    verified = verify_single_citation(original_citation)

    # 1996 should override 2069 since 2069 is wildly out of bounds, or we should prefer the regex extracted year!
    assert "1996" in verified
    assert "2069" not in verified
