import json
from src.verifier import verify_references_block

with open("assets/sample3_output.json") as f:
    data = json.load(f)

refs = data["references"]
print("Original format preview:")
print(refs[:500])

import re
# Testing split
raw_citations = re.split(r'\n(?=\[\d+\]|\d+\.)|\n{2,}', refs)
citations = [c.strip() for c in raw_citations if len(c.strip()) > 15]
print("\nNumber of citations split:", len(citations))
for i, c in enumerate(citations[:3]):
    print(f"[{i}]: {c[:100]}...")
