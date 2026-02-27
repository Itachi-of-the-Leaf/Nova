import sys
sys.path.append("backend")
from src.formatter import _latex_escape

test_string = "Math: ⊆ ∈ ∉ α β γ Δ δ ε θ λ μ π σ Σ Φ Ω ± × ÷ ≈ ≠ ≤ ≥ ∞ ° ← ↔ ⇒ є Π ∅ ∗ ∩ ∪ ∼ ⟨ ⟩"
escaped = _latex_escape(test_string)

missing = []
for expected in [r'\subseteq', r'\in', r'\notin', r'\alpha', r'\approx', r'\cap']:
    if expected not in escaped:
        missing.append(expected)

print("ESCAPED:", escaped)
if missing:
    print("FAILED MATH ESCAPE REGRESSION:", missing)
else:
    print("ALL MATH SYMBOLS PRESERVED AND ESCAPED CORRECTLY!")
