import sys
sys.path.append("backend")
from unstructured.partition.auto import partition
elements = partition("assets/Sample_X_Input.docx", strategy="hi_res", hi_res_model_name="yolox", infer_table_structure=True, skip_infer_table_types=[])
table_count = 0
for e in elements:
    t = type(e).__name__
    if t == "Table" or "Table" in t:
        table_count += 1
        html = getattr(e.metadata, "text_as_html", "NO_HTML") if hasattr(e, "metadata") else "NO_HTML"
        print(f"--- TABLE {table_count} ---")
        print("HTML length:", len(html))
        print("HTML content preview:", html[:200])
        print("Text preview:", e.text[:100])
print(f"Found {table_count} tables.")
