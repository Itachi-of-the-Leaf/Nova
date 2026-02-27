import sys
sys.path.append("backend")

from unstructured.partition.auto import partition
print("Extracting Sample X tables directly with chunks...")
elements = partition(
    filename="assets/Sample_X_Input.docx",
    strategy="hi_res",
    hi_res_model_name="yolox",
    infer_table_structure=True,
    skip_infer_table_types=["pdf"],
    chunking_strategy="by_title",
    combine_text_under_n_chars=500,
    max_characters=2000,
    languages=["eng"]
)

for e in elements:
    if "Table" in type(e).__name__ or "Composite" in type(e).__name__ or "Table" in getattr(e, "text", ""):
        print(f"[{type(e).__name__}]:", getattr(e, "text", "")[:100].replace("\n", " "))
