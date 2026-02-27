import sys
sys.path.append("backend")
from unstructured.partition.auto import partition
elements = partition("assets/Sample_3_Input.docx", strategy="hi_res", hi_res_model_name="yolox", infer_table_structure=True, skip_infer_table_types=[])
for e in elements:
    t = type(e).__name__
    if t == "Table" or "Table" in t:
        print("FOUND TABLE:", e.text)
print("Finished.")
