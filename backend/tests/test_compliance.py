import pytest
from src.engine import fix_and_shorten_abstract

def test_fix_abstract_preserves_text_for_detector_evasion():
    sample = "This is a brilliantly erratic human string featuring extremely high perplexity and burstiness."
    out = fix_and_shorten_abstract(sample)
    
    # Mathematical identity check ensures no AI alteration occurred
    assert out == sample

