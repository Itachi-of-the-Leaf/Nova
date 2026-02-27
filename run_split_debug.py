import json, re

with open("assets/Sample_3_Input_output.json") as f:
    data = json.load(f)

raw_refs = data["references"][0]
print("Raw refs preview:", raw_refs[:300])

# Split by looking for 4-digit years followed by a period, then a space, then a Capital letter
# Example: 2012.  Scott Aaronson
citations_split = re.split(r'(?<=\d{4}\.)\s+(?=[A-Z])', raw_refs)
print("Number of citations:", len(citations_split))
for i, c in enumerate(citations_split[:3]):
    print(f"[{i}]: {c[:100]}...")

