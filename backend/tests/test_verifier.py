import pytest
from src.verifier import verify_single_citation

def test_verify_single_citation_returns_constructed():
    messy = "attention is all you need vaswani et al 2017"
    result = verify_single_citation(messy)
    
    # Must be verified
    assert "✅ [VERIFIED" in result
    # We expect the actual title and author, not just our messy string
    assert "Attention is all you need" in result.title() or "Attention Is All You Need" in result.title()
    assert "Ashish Vaswani" in result
    # We specifically don't want the messy text appended like the old vulnerable version did
    assert messy not in result

def test_verify_single_citation_hallucination():
    fake = "Vaswani, A. (2027). Time traveling with transformers. Journal of Fake Science."
    result = verify_single_citation(fake)
    assert "NOT FOUND" in result or "LOW CONFIDENCE" in result
    assert "VERIFIED" not in result
